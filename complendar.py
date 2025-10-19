#!/usr/bin/env python3
import functools
import http.server
import json
import socketserver
import sys
import urllib.parse
from csv import DictReader
from datetime import date, datetime, timedelta
from hashlib import sha3_256
from io import BytesIO, TextIOWrapper
from pathlib import Path
from re import compile as com
from tempfile import gettempdir
from typing import Iterable, NamedTuple, Optional, Tuple, Union
from uuid import UUID, uuid4

import httpx
from ical.alarm import Action, Alarm
from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event
from ical.recurrence import Recur
from ical.types import Frequency

# ---------------- CONFIG ----------------
SPREADSHEET_LINK = com(
    r"^https://docs\.google\.com/spreadsheets/d/(?P<spreadsheet_id>[^/]{44})/(.*)?(\?(?P<query_params>.*))?"
)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


# ---------------- DATA MODEL ----------------
class Entry(NamedTuple):
    name: str
    date: date

    def to_event(self) -> Event:
        possessive = "'" if self.name.endswith("s") else "'s"
        event_hash = sha3_256(
            f"{self.name} {self.date.isoformat()}".encode()
        ).hexdigest()[:32]
        return Event(
            uid=f"{UUID(event_hash)}@complendar.event",
            summary=f"{self.name}{possessive} Birthday",
            description=f"Celebrate {self.name}'s birthday 🎂",
            categories=["BIRTHDAY"],
            start=self.date,
            transparency="TRANSPARENT",
            rrule=Recur(freq=Frequency.YEARLY),
            alarm=[
                Alarm(
                    action=Action.DISPLAY,
                    trigger=timedelta(days=-1),
                    description=f"Tomorrow is {self.name}{possessive} birthday!",
                ),
                Alarm(
                    action=Action.DISPLAY,
                    trigger=timedelta(hours=0),
                    description=f"Today is {self.name}{possessive} birthday! 🎉",
                ),
            ],
        )


# ---------------- CORE LOGIC ----------------
def _get_csv_from_sheets(spreadsheet_link: str) -> BytesIO:
    m = SPREADSHEET_LINK.match(spreadsheet_link)
    if not m:
        raise ValueError("Invalid spreadsheet link")

    spreadsheet_id = m["spreadsheet_id"]
    query_params = f"?{m['query_params']}" if m["query_params"] else ""

    csv_url: str = f"https://docs.google.com/spreadsheets/d/{m['spreadsheet_id']}/export?format=csv{query_params}"
    r: httpx.Response = httpx.get(url=csv_url, follow_redirects=True)
    r.raise_for_status()
    return BytesIO(r.read())


def _jaccard_similarity(a: str, b: str) -> float:
    s_a = set(a.lower())
    s_b = set(b.lower())
    return len(s_a.intersection(s_b)) / len(s_a.union(s_b))


def _guess_headers_from_reader_fieldnames(reader: DictReader) -> Tuple[str, str]:
    fieldnames = list(reader.fieldnames)  # noqa

    def _most_similar_header(prompt):
        return sorted(
            fieldnames, key=lambda x: _jaccard_similarity(prompt, x), reverse=True
        )[0]

    return _most_similar_header("your name"), _most_similar_header("your birthday")


def _parse_row(row, name_header: str, birthday_header: str) -> Optional[Entry]:
    name = row.get(name_header, None)
    birthday = row.get(birthday_header, None)
    try:
        birthday_dt: Optional[datetime] = datetime.strptime(birthday, "%m/%d/%Y")
    except (ValueError, TypeError):
        return None
    return Entry(name=name, date=birthday_dt.date()) if name else None


def _format_csv(csv_bytes: BytesIO) -> tuple[Iterable[Optional[Entry]], Tuple[str, str]]:
    with TextIOWrapper(csv_bytes) as f:
        reader = DictReader(f.readlines())
        if not reader.fieldnames:
            raise ValueError("Empty CSV. There is no data to parse.")
        name_header, birthday_header = _guess_headers_from_reader_fieldnames(reader)
        rows = map(lambda x: _parse_row(x, name_header, birthday_header), reader)
        return rows, (name_header, birthday_header)


def _convert_entries_to_ics(entries: Iterable[Union[Entry, None]]) -> str:
    events = [e.to_event() for e in entries if e]
    cal = Calendar(events=events, prodid="-//Complendar//EN", version="2.0")
    return IcsCalendarStream.calendar_to_ics(cal)


# ---------------- CLI MODE ----------------
def cli_main(link: str, output: Optional[str] = None):
    print(f"Fetching CSV from: {link}")
    csv_bytes = _get_csv_from_sheets(link)
    print("Parsing CSV…")
    entries, (name_header, birthday_header) = _format_csv(csv_bytes)
    print(f"Guessed headers\n→ Name: \"{name_header}\"\n→ Birthday: \"{birthday_header}\"")
    print("Converting to ICS…")
    ical = _convert_entries_to_ics(entries)
    output_path = Path(output or f"complendar_{uuid4().hex}.ics")
    output_path.write_text(ical, encoding="utf-8")
    print(f"✅ Done. Saved to {output_path}")


# ---------------- WEB SERVER ----------------
class ComplendarHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/convert":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            try:
                link = data.get("link")
                csv_bytes = _get_csv_from_sheets(link)
                entries, headers = _format_csv(csv_bytes)
                ical = _convert_entries_to_ics(entries)
                filename = f"complendar_{uuid4().hex}.ics"
                file_path = Path(gettempdir()) / filename
                file_path.write_text(ical, encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "file": f"/download/{filename}",
                    "guessed_headers": {"name": headers[0], "birthday": headers[1]}
                }).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        else:
            self.send_error(404)

    def do_GET(self):
        if self.path.startswith("/download/"):
            filename = self.path.split("/")[-1]
            file_path = Path(gettempdir()) / filename
            if file_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/calendar")
                self.send_header(
                    "Content-Disposition", f"attachment; filename={filename}"
                )
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_error(404)
        else:
            if self.path == "/":
                self.path = "/index.html"
            return super().do_GET()


def run_web_server():
    PORT = 8000
    handler = functools.partial(ComplendarHandler, directory=str(STATIC_DIR))
    print(f"🌐 Running on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        run_web_server()
