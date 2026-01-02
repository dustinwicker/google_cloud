# Google Cloud

Python utilities for interacting with Google Cloud services, specifically Google Sheets and Google Drive APIs.

## Features

- **Google Sheets Integration** - Read and parse data from Google Sheets
- **Packing List Parser** - Retrieves items from a packing list spreadsheet, filtering out strikethrough (completed) items
- **Credit Card Tracker** - Calculates and updates monthly totals for non-strikethrough credit card expenses
- **Service Account Authentication** - Secure authentication using Google service account credentials

## Setup

### Prerequisites

- Python 3.x
- Google Cloud project with Sheets and Drive APIs enabled
- Service account credentials JSON file

### Installation

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install google-api-python-client google-auth
```

### Environment Variables

Set the following environment variables:

```bash
export GOOGLE_SERVICE_ACCOUNT="/path/to/service-account-credentials.json"
export GOOGLE_SHEET_PACKING_LIST_ID="your-spreadsheet-id"
export GOOGLE_SHEET_SHEET_ONE="Sheet1!A1:Z100"
```

## Usage

### Packing List Script

Retrieves remaining (non-strikethrough) items from a Google Sheets packing list:

```bash
python packing_list.py
```

The script will:
- Connect to your Google Sheets packing list
- Filter out items marked with strikethrough formatting
- Display the remaining items and completion percentage

### Credit Card Tracker Script

Calculates monthly totals for non-strikethrough credit card expenses and updates the "Total Remaining" row:

```bash
python credit_card_tracker.py
```

The script will:
- Access the Finances sheet in your credit card spreadsheet
- Calculate monthly totals for each month column (October, November, December, January, etc.)
- Only sum amounts from cells that are NOT strikethrough
- Update the "Total Remaining" row with the calculated totals

**Note:** The spreadsheet ID is hardcoded in the script, but can be overridden via command line or environment variable.

## Files

| File | Description |
|------|-------------|
| `packing_list.py` | Script to retrieve and display remaining items from a Google Sheets packing list |
| `credit_card_tracker.py` | Script to calculate and update monthly totals for credit card expenses |
| `creds.py` | Authentication module using Google service account |
| `requirements.txt` | Python package dependencies |

## License

MIT
