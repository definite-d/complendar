from datetime import date
from ics import Calendar, Event
from typing import NamedTuple, Tuple
from os import environ as env
from dotenv import load_dotenv
from csv import DictReader
import httpx
from re import compile as com
from io import BytesIO, TextIOWrapper

load_dotenv()


SPREADSHEET_LINK = com(
    r"^https://docs.google.com/spreadsheets/d/(?P<spreadsheet_id>[^/]{44})/.*\?(?P<query_params>.*)"
)


class Entry(NamedTuple):
    name: str
    date: date


def _get_csv_from_sheets(spreadsheet_link) -> BytesIO:
    """
    Gets the result of the Google Form as a CSV from Google Docs
    """
    m = SPREADSHEET_LINK.match(spreadsheet_link)
    if not m:
        raise ValueError("Invalid spreadsheet link")

    csv_url: str = f"https://docs.google.com/spreadsheets/d/{m['spreadsheet_id']}/export?format=csv&{m['query_params']}"
    try:
        r: httpx.Response = httpx.get(url=csv_url, follow_redirects=True)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        if r.status_code == 401:
            raise ValueError(
                "Access denied. Perhaps the spreadsheet is not publicly shared?"
            ) from e
        else:
            raise e

    return BytesIO(r.read())


def _jaccard_similarity(a: str, b: str) -> float:
    s_a = set(a.lower())
    s_b = set(b.lower())
    return len(s_a.intersection(s_b)) / len(s_a.union(s_b))


def _headers_from_reader_fieldnames(reader: DictReader) -> Tuple[str, str]:
    fieldnames = list(reader.fieldnames)  # noqa

    def _most_similar_header(prompt):
        return sorted(
            fieldnames, key=lambda x: _jaccard_similarity(prompt, x), reverse=True
        )[0]

    return _most_similar_header("your name"), _most_similar_header("your birthday")


def _format_csv(csv_bytes: BytesIO):
    with TextIOWrapper(csv_bytes) as f:
        reader = DictReader(f.readlines())
        if not reader.fieldnames:
            raise ValueError("Empty CSV. There is no data to parse.")
            
        name_header, birthday_header = _headers_from_reader_fieldnames(reader)
        print(name_header, birthday_header)
        for line in reader:
            print(line)


def main():
    form_link = env.get("COMPLENDAR_SPREADSHEET_URL") or input(
        "Please enter the link to the Google Forms' Spreadsheet: "
    )
    csv_bytes = _get_csv_from_sheets(form_link)
    _format_csv(csv_bytes)


if __name__ == "__main__":
    main()
