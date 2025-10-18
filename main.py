from datetime import date
from ics import Calendar, Event
from typing import NamedTuple
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


def _format_csv(csv_bytes: BytesIO):
    with TextIOWrapper(csv_bytes) as f:
        reader = DictReader(f.readlines())
        for line in reader:
            print(line)


def main():
    form_link = env.get("COMPLENDAR_SPREADSHEET_URL") or input(
        "Please enter the link to the Google Forms' Spreadsheet: "
    )
    csv_data = _get_csv_from_sheets(form_link)
    _format_csv(csv_data)


if __name__ == "__main__":
    main()
