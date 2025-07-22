import sys
sys.path.append('/Users/dustinwicker/projects/google_cloud')
import creds
import os
from googleapiclient.discovery import build

def main():
    # Use the login function from creds.py to obtain the credentials
    credentials = creds.login()
    print("Credentials obtained successfully")
    return credentials


def get_packing_list(spreadsheet_id: str, range_name: str):
    """
    Retrieves all data from a Google Sheets document and returns the data as a list of dictionaries.

    :param spreadsheet_id: The ID of the Google Sheets document (string)
    :param range_name: The name of the sheet to retrieve data from (string), ex. 'Sheet1!A1:Z100'
    :return: A list of dictionaries where each dictionary represents a row of data in the sheet.
    """
    sheet = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        majorDimension='ROWS').execute()  # 'ROWS' or 'COLUMNS'
    values = sheet.get('values')
    if values:
        # Find the last row of the sheet
        last_row = len(values)
        # Find the last column of the sheet
        last_col = 0
        for row in values:
            last_col = max(last_col, len(row))
        # If there are columns A-Z, second_letter should be 'Z', for example
        second_letter = str.capitalize(chr(ord('a') + last_col - 1))
        # Update the range_name to the entire sheet
        range_name = f'Sheet1!A1:{second_letter}{last_row}'
    # Retrieve the entire sheet as a list of dictionaries
    sheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id, ranges=range_name,
                                       includeGridData=True).execute()
    sheets = sheet.get('sheets')
    data = sheets[0].get('data', [])
    grid_data = data[0]
    packing_list = grid_data.get('rowData', [])
    return packing_list


def get_remaining_items_from_packing_list(packing_list: list):
    for row in packing_list:
        values = row.get('values', [])
        if not values[0].get('userEnteredFormat').get('textFormat').get('strikethrough'):
            value = values[0].get('userEnteredValue')
            print(value.get('stringValue'))


if __name__ == "__main__":
    credentials = main()
    service = build('sheets', 'v4', credentials=credentials)
    spreadsheet_id, range_name = os.environ.get('GOOGLE_SHEET_PACKING_LIST_ID'), os.environ.get('GOOGLE_SHEET_SHEET_ONE')
    packing_list = get_packing_list(spreadsheet_id, range_name)
    get_remaining_items_from_packing_list(packing_list)
