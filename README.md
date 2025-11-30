# Google Cloud

Python utilities for interacting with Google Cloud services, specifically Google Sheets and Google Drive APIs.

## Features

- **Google Sheets Integration** - Read and parse data from Google Sheets
- **Packing List Parser** - Retrieves items from a packing list spreadsheet, filtering out strikethrough (completed) items
- **Service Account Authentication** - Secure authentication using Google service account credentials

## Setup

### Prerequisites

- Python 3.x
- Google Cloud project with Sheets and Drive APIs enabled
- Service account credentials JSON file

### Installation

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

```python
from creds import login
from googleapiclient.discovery import build

# Authenticate
credentials = login()
service = build('sheets', 'v4', credentials=credentials)

# Get packing list items (excluding strikethrough items)
packing_list = get_packing_list(spreadsheet_id, range_name)
get_remaining_items_from_packing_list(packing_list)
```

## Files

| File | Description |
|------|-------------|
| `main.py` | Main script for retrieving and parsing Google Sheets data |
| `creds.py` | Authentication module using Google service account |

## License

MIT
