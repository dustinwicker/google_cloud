import creds
import os
from googleapiclient.discovery import build

def main():
    # Use the login function from creds.py to obtain the credentials
    credentials = creds.login()
    print("Credentials obtained successfully")
    return credentials

if __name__ == "__main__":
    credentials = main()

service = build('sheets', 'v4', credentials=credentials)
# spreadsheet_id = os.environ.get('GOOGLE_SHEET_PACKING_LIST_ID')
# range_name = os.environ.get('GOOGLE_SHEET_PACKING_LIST_SHEET_NAME')
#
# v = service.spreadsheets().values().get(
#     spreadsheetId=spreadsheet_id,
#     range=range_name,
#     majorDimension='ROWS'  # 'ROWS' or 'COLUMNS'
# ).execute()
# values = v.get('values')
# if values:
#     last_row = len(values)
#     last_col = 0
#     for row in values:
#         last_col = max(last_col, len(row))
# second_letter = str.capitalize(chr(ord('a') + last_col-1))
# range_name = f'Sheet1!A1:{second_letter}{79}'
# sheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id,
#                                             ranges=range_name,
#                                             includeGridData=True).execute()
# sheets = sheet.get('sheets')
# data = sheets[0].get('data', [])
# grid_data = data[0]
# row_data = grid_data.get('rowData', [])
# for row in row_data:
#     values = row.get('values', [])
#     if not values[0].get('userEnteredFormat').get(
#     'textFormat').get('strikethrough'):
#         print(values[0].get('userEnteredValue'), values[0].get('userEnteredFormat').get(
#         'textFormat').get('strikethrough'))
#
# sheet.get('sheets')[0].get('data')[0].get('rowData')[0].get('values')[0].get('userEnteredValue')
# sheet.get('sheets')[0].get('data')[0].get('rowData')[0].get('values')[0].get('userEnteredFormat').get(
#     'textFormat').get('strikethrough')