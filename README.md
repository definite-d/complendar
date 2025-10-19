# 🎉 Complendar: Convert Google Sheet Forms to Calendar Events

Complendar is a simple, self-hosted Python utility that takes a public Google Sheet (typically generated from a Google Form) and converts the list of names and birthdays into a standard **$\text{.ics}$ calendar file**. This file can then be imported into any calendar application (Google, Outlook, Apple, etc.) to create **yearly recurring birthday events**.

It supports both a simple **Command-Line Interface ($\text{CLI}$)** and a **Web Interface**.

## Quick Start (Web Interface)

Use `uv` to install and run the project from a local clone.

### Preliminaries

1.  **Google Sheet Link:** Ensure you have the public link to the Google Sheet that contains your name and birthday data. This sheet must have column headers that clearly indicate the **Name** and **Date** fields (e.g., "Your Name", "Birthday").
2.  **Required Tool:** You'll need the [`uv`](https://www.google.com/search?q=%5Bhttps://github.com/astral-sh/uv%5D\(https://github.com/astral-sh/uv\)) tool for fast dependency management and running the project.

### 1\. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/your-username/complendar.git
cd complendar
uv sync
```

### 2\. Run the Web Server

Run the Python module to start the web server on $\text{port 8000}$.

```bash
uv run python -m complendar
```

This will output:

```
🌐 Running on http://localhost:8000
```

### 3\. Usage

1.  Open your browser to **`http://localhost:8000`**.
2.  Paste your public Google Sheet link into the input box.
3.  Click **"Convert to ICS"**.
4.  The system will fetch, parse, and convert the data. Once complete, click the **"⬇️ Download ICS"** link to save the file.

-----

## CLI Usage

For power users, Complendar can be run directly from the terminal, bypassing the web interface.

### Syntax

```bash
uv run python -m complendar <SPREADSHEET_LINK> [OUTPUT_FILE_NAME]
```

### Example

```bash
uv run python -m complendar "https://docs.google.com/spreadsheets/d/12345EXAMPLE_SHEET_ID/edit#gid=0" birthdays.ics

# Output:
# Fetching CSV from: https://docs.google.com/spreadsheets/d/12345EXAMPLE_SHEET_ID/edit#gid=0
# Parsing CSV…
# Guessed headers
# → Name: "Your Name"
# → Birthday: "Your Birthday"
# Converting to ICS…
# ✅ Done. Saved to birthdays.ics
```

-----

## Importing the $\text{.ics}$ File into Your Calendar

The generated **$\text{.ics}$** file contains **recurring yearly events** with reminders set for the day before and the day of each birthday. You need to **import** this file into your chosen calendar application.

| Calendar Application | How to Import (Official Guide) |
| :--- | :--- |
| **Google Calendar** | [Import events into Google Calendar](https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform%3DDesktop) |
| **Microsoft Outlook** | [Import or subscribe to a calendar in Outlook.com or Outlook on the web](https://support.microsoft.com/en-us/office/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web-cff1429c-5af6-41ec-a5b4-74f2c278e98c) |
| **Apple Calendar (Mac)** | [Import or export calendars on Mac](https://support.apple.com/guide/calendar/import-or-export-calendars-icl1023/mac) |

**Note on Recurring Events:** When importing, ensure your calendar is set to include all future occurrences of these yearly recurring events.