#!/usr/bin/env python3
import creds
import os
import sys
from googleapiclient.discovery import build
from datetime import datetime

# Default spreadsheet ID for credit card tracker
DEFAULT_SPREADSHEET_ID = '1UcNU8cT6OWKouLgy5QGtfzYkFd7b0yq3qyFphCAfmLw'

def get_credentials():
    """Get Google Sheets credentials."""
    credentials = creds.login()
    print("Credentials obtained successfully")
    return credentials


def get_sheet_data(service, spreadsheet_id: str, range_name: str = None):
    """
    Retrieves all data from a Google Sheets document with formatting information.
    
    :param service: The Google Sheets service object
    :param spreadsheet_id: The ID of the Google Sheets document
    :param range_name: Optional range name (e.g., 'Sheet1!A1:Z100'). If None, gets entire first sheet.
    :return: A tuple of (row_data with formatting, values without formatting)
    """
    # First, get basic info about the spreadsheet
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    if not sheets:
        print("No sheets found in spreadsheet")
        return [], []
    
    # Determine which sheet to use
    if range_name and '!' in range_name:
        # Extract sheet name from range (e.g., "Finances!A1:Z100")
        sheet_title = range_name.split('!')[0]
    elif range_name:
        # range_name is just the sheet name
        sheet_title = range_name
    else:
        # Use first sheet
        sheet_title = sheets[0].get('properties', {}).get('title')
    
    print(f"\nAccessing sheet: '{sheet_title}'")
    
    # Get values first to determine range
    if range_name is None or (range_name and '!' not in range_name):
        # Get all values to determine the range
        values_result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_title
        ).execute()
        values = values_result.get('values', [])
        
        if not values:
            print("No data found in sheet")
            return [], []
        
        # Calculate range
        last_row = len(values)
        last_col = 0
        for row in values:
            last_col = max(last_col, len(row))
        
        if last_col > 0:
            # Convert column number to letter (A=1, Z=26, AA=27, etc.)
            col_letter = ''
            col_num = last_col
            while col_num > 0:
                col_num -= 1
                col_letter = chr(65 + (col_num % 26)) + col_letter
                col_num //= 26
            range_name = f'{sheet_title}!A1:{col_letter}{last_row}'
        else:
            range_name = sheet_title
    else:
        # Get values for the specified range
        values_result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        values = values_result.get('values', [])
    
    # Get detailed data with formatting
    sheet_data = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=range_name,
        includeGridData=True
    ).execute()
    
    sheets_data = sheet_data.get('sheets', [])
    if sheets_data:
        data = sheets_data[0].get('data', [])
        if data:
            row_data = data[0].get('rowData', [])
            return row_data, values
    
    return [], values


def display_sheet_info(service, spreadsheet_id: str):
    """Display information about the spreadsheet."""
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    props = spreadsheet.get('properties', {})
    
    print(f"\n{'='*60}")
    print(f"Spreadsheet: {props.get('title', 'Untitled')}")
    print(f"ID: {spreadsheet_id}")
    print(f"{'='*60}")
    
    sheets = spreadsheet.get('sheets', [])
    print(f"\nSheets in spreadsheet ({len(sheets)}):")
    for i, sheet in enumerate(sheets, 1):
        sheet_props = sheet.get('properties', {})
        grid_props = sheet_props.get('gridProperties', {})
        print(f"  {i}. {sheet_props.get('title')} "
              f"({grid_props.get('rowCount', 0)} rows × {grid_props.get('columnCount', 0)} cols)")


def sum_by_month_non_strikethrough(service, spreadsheet_id: str, sheet_name: str = 'Finances'):
    """
    Sum amounts by month for rows that are NOT strikethrough.
    
    :param service: The Google Sheets service object
    :param spreadsheet_id: The ID of the Google Sheets document
    :param sheet_name: Name of the sheet to process
    :return: Dictionary with month names as keys and sums as values
    """
    # Get the sheet data with formatting
    row_data, values = get_sheet_data(service, spreadsheet_id, range_name=sheet_name)
    
    if not row_data or not values:
        print("No data found in sheet")
        return {}
    
    # Find the month header row (should have "October", "November", etc.)
    month_row_idx = None
    month_columns = {}  # {month_name: column_index}
    
    for i, row in enumerate(values):
        for j, cell in enumerate(row):
            if isinstance(cell, str) and cell.strip() in ['October', 'November', 'December', 'January', 
                                                           'February', 'March', 'April', 'May', 'June', 
                                                           'July', 'August', 'September']:
                if month_row_idx is None:
                    month_row_idx = i
                month_columns[cell.strip()] = j
    
    if not month_columns:
        print("Could not find month headers in sheet")
        return {}
    
    print(f"\nFound months: {list(month_columns.keys())}")
    print(f"Month header row: {month_row_idx + 1}")
    
    # Find the data rows (rows after the header, before totals)
    # Look for rows that have amounts in the month columns
    data_rows = []
    for i in range(month_row_idx + 2, len(values)):  # Start after month header + column header
        row = values[i]
        row_format = row_data[i] if i < len(row_data) else None
        
        # Skip empty rows and total/summary rows
        if not row or not row[0]:
            continue
        if isinstance(row[0], str) and ('Total' in row[0] or 'Amount' in row[0] or row[0].startswith('==')):
            continue
        
        # Check if this row has any amounts in month columns
        has_amount = False
        for month, col_idx in month_columns.items():
            if col_idx < len(row) and row[col_idx]:
                try:
                    # Try to parse as number
                    amount = float(str(row[col_idx]).replace(',', '').replace('$', ''))
                    if amount != 0:
                        has_amount = True
                        break
                except:
                    pass
        
        if has_amount:
            data_rows.append((i, row, row_format))
    
    print(f"Found {len(data_rows)} data rows to process\n")
    
    # Sum by month for non-strikethrough rows
    monthly_totals = {month: 0.0 for month in month_columns.keys()}
    
    for row_idx, row, row_format in data_rows:
        # Check strikethrough for each month column individually (per cell, not per row)
        row_name = row[0] if row else f"Row {row_idx + 1}"
        for month, col_idx in month_columns.items():
            # Check if this specific cell is strikethrough
            is_cell_strikethrough = False
            if row_format and row_format.get('values') and col_idx < len(row_format.get('values', [])):
                cell_format = row_format.get('values', [{}])[col_idx]
                text_format = cell_format.get('userEnteredFormat', {}).get('textFormat', {})
                is_cell_strikethrough = text_format.get('strikethrough', False)
            
            # Only sum if this cell is NOT strikethrough
            if not is_cell_strikethrough and col_idx < len(row) and row[col_idx]:
                try:
                    amount = float(str(row[col_idx]).replace(',', '').replace('$', ''))
                    monthly_totals[month] += amount
                except (ValueError, TypeError):
                    pass
    
    return monthly_totals


def update_total_remaining_row(service, spreadsheet_id: str, sheet_name: str = 'Finances'):
    """
    Update the "Total Remaining" row with sums of non-strikethrough rows for each month.
    
    :param service: The Google Sheets service object
    :param spreadsheet_id: The ID of the Google Sheets document
    :param sheet_name: Name of the sheet to process
    :return: True if successful, False otherwise
    """
    # Get the sheet data with formatting
    row_data, values = get_sheet_data(service, spreadsheet_id, range_name=sheet_name)
    
    if not row_data or not values:
        print("No data found in sheet")
        return False
    
    # Find the month header row and columns
    month_row_idx = None
    month_columns = {}  # {month_name: column_index}
    
    for i, row in enumerate(values):
        for j, cell in enumerate(row):
            if isinstance(cell, str) and cell.strip() in ['October', 'November', 'December', 'January', 
                                                           'February', 'March', 'April', 'May', 'June', 
                                                           'July', 'August', 'September']:
                if month_row_idx is None:
                    month_row_idx = i
                month_columns[cell.strip()] = j
    
    if not month_columns:
        print("Could not find month headers in sheet")
        return False
    
    # Find the "Total Remaining" row
    # First try to find it by label
    total_remaining_row_idx = None
    for i, row in enumerate(values):
        if row and isinstance(row[0], str) and 'Total Remaining' in row[0]:
            total_remaining_row_idx = i
            break
    
    # If not found by label, try to find it by position (usually row 19, index 18)
    # Look for a row that comes after data rows but before "Total" row
    if total_remaining_row_idx is None:
        # Find the "Total" row first to know where to stop looking
        total_row_idx = None
        for i, row in enumerate(values):
            if row and isinstance(row[0], str) and row[0].strip() == 'Total':
                total_row_idx = i
                break
        
        # The "Total Remaining" row should be right before the "Total" row
        if total_row_idx and total_row_idx > 0:
            total_remaining_row_idx = total_row_idx - 1
            print(f"Found 'Total Remaining' row by position (row {total_remaining_row_idx + 1}, before 'Total' row)")
        else:
            # Fallback: use row 19 (index 18) if it exists
            if len(values) > 18:
                total_remaining_row_idx = 18
                print(f"Using row 19 as 'Total Remaining' row (default position)")
    
    if total_remaining_row_idx is None:
        print("Could not find 'Total Remaining' row")
        return False
    
    print(f"\nFound 'Total Remaining' row at row {total_remaining_row_idx + 1}")
    
    # Find the data rows (rows between header and total remaining)
    data_row_indices = []
    for i in range(month_row_idx + 2, total_remaining_row_idx):  # Start after month header + column header, before total
        row = values[i]
        row_format = row_data[i] if i < len(row_data) else None
        
        # Skip empty rows
        if not row or not row[0]:
            continue
        # Skip if it's a summary/total row
        if isinstance(row[0], str) and ('Total' in row[0] or row[0].startswith('==')):
            continue
        
        # Check if this row has any amounts in month columns
        has_amount = False
        for month, col_idx in month_columns.items():
            if col_idx < len(row) and row[col_idx]:
                try:
                    amount = float(str(row[col_idx]).replace(',', '').replace('$', ''))
                    if amount != 0:
                        has_amount = True
                        break
                except:
                    pass
        
        if has_amount:
            data_row_indices.append(i)
    
    print(f"Found {len(data_row_indices)} data rows to sum (rows {min(data_row_indices)+1 if data_row_indices else 0} to {max(data_row_indices)+1 if data_row_indices else 0})")
    
    # Calculate totals for each month column
    monthly_totals = {month: 0.0 for month in month_columns.keys()}
    
    for row_idx in data_row_indices:
        row = values[row_idx]
        row_format = row_data[row_idx] if row_idx < len(row_data) else None
        
        # Check strikethrough for each month column individually (per cell, not per row)
        for month, col_idx in month_columns.items():
            # Check if this specific cell is strikethrough
            is_cell_strikethrough = False
            if row_format and row_format.get('values') and col_idx < len(row_format.get('values', [])):
                cell_format = row_format.get('values', [{}])[col_idx]
                text_format = cell_format.get('userEnteredFormat', {}).get('textFormat', {})
                is_cell_strikethrough = text_format.get('strikethrough', False)
            
            # Only sum if this cell is NOT strikethrough
            if not is_cell_strikethrough and col_idx < len(row) and row[col_idx]:
                try:
                    amount = float(str(row[col_idx]).replace(',', '').replace('$', ''))
                    monthly_totals[month] += amount
                except (ValueError, TypeError):
                    pass
    
    # Prepare the update - convert column indices to A1 notation
    def col_index_to_letter(col_idx):
        """Convert 0-based column index to letter (0=A, 25=Z, 26=AA, etc.)"""
        result = ''
        col_idx += 1  # Convert to 1-based
        while col_idx > 0:
            col_idx -= 1
            result = chr(65 + (col_idx % 26)) + result
            col_idx //= 26
        return result
    
    # Build the update values - only update the month columns
    # We'll update each month column individually to preserve other columns
    updates = []
    for month, col_idx in month_columns.items():
        col_letter = col_index_to_letter(col_idx)
        range_name = f"{sheet_name}!{col_letter}{total_remaining_row_idx + 1}"
        updates.append({
            'range': range_name,
            'values': [[monthly_totals[month]]]
        })
    
    # Batch update all month columns at once
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': updates
    }
    
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    
    # Get the range for display
    min_col = min(month_columns.values()) if month_columns else 0
    max_col = max(month_columns.values()) if month_columns else 0
    range_name = f"{sheet_name}!{col_index_to_letter(min_col)}{total_remaining_row_idx + 1}:{col_index_to_letter(max_col)}{total_remaining_row_idx + 1}"
    
    
    print(f"\n✓ Updated 'Total Remaining' row successfully!")
    print(f"  Range updated: {range_name}")
    print(f"\nMonthly totals written to 'Total Remaining' row:")
    for month in sorted(month_columns.keys(), key=lambda x: ['January', 'February', 'March', 'April', 
                                                              'May', 'June', 'July', 'August', 
                                                              'September', 'October', 'November', 'December'].index(x) if x in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'] else 999):
        if month in monthly_totals:
            print(f"  {month:12} ${monthly_totals[month]:>12,.2f}")
    
    return True


def display_sheet_data(row_data: list, values: list, max_rows: int = 20):
    """
    Display the sheet data with formatting information.
    
    :param row_data: Row data with formatting
    :param values: Plain values
    :param max_rows: Maximum number of rows to display
    """
    if not values:
        print("\nNo data to display")
        return
    
    print(f"\n{'='*60}")
    print(f"Sheet Data (showing first {min(max_rows, len(values))} rows)")
    print(f"{'='*60}\n")
    
    for row_idx, (row_format, row_values) in enumerate(zip(row_data[:max_rows], values[:max_rows]), 1):
        print(f"Row {row_idx}:")
        
        # Check if row is strikethrough
        is_strikethrough = False
        if row_format and row_format.get('values'):
            first_cell = row_format.get('values', [{}])[0]
            text_format = first_cell.get('userEnteredFormat', {}).get('textFormat', {})
            is_strikethrough = text_format.get('strikethrough', False)
        
        status = " [STRUCK THROUGH]" if is_strikethrough else " [ACTIVE]"
        print(f"  Status: {status}")
        
        # Display cell values
        cell_values = row_format.get('values', []) if row_format else []
        for col_idx, (cell_format, cell_value) in enumerate(zip(cell_values, row_values), 1):
            # Get the actual value
            if cell_format and cell_format.get('userEnteredValue'):
                user_value = cell_format.get('userEnteredValue')
                if 'numberValue' in user_value:
                    display_value = user_value.get('numberValue')
                elif 'stringValue' in user_value:
                    display_value = user_value.get('stringValue')
                elif 'formulaValue' in user_value:
                    display_value = f"={user_value.get('formulaValue')}"
                else:
                    display_value = cell_value if cell_value else ""
            else:
                display_value = cell_value if cell_value else ""
            
            print(f"    Col {col_idx}: {display_value}")
        print()


if __name__ == "__main__":
    # Get credentials and build service
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    
    # Get spreadsheet ID from command line, environment variable, default, or prompt
    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
    else:
        spreadsheet_id = os.environ.get('GOOGLE_SHEET_CREDIT_CARD_ID') or DEFAULT_SPREADSHEET_ID
    
    if not spreadsheet_id:
        print("\n⚠️  No spreadsheet ID found")
        print("Usage: python credit_card_tracker.py [spreadsheet-id]")
        print("   OR: export GOOGLE_SHEET_CREDIT_CARD_ID='your-id' && python credit_card_tracker.py")
        print("   OR: Enter it now (or press Ctrl+C to cancel)")
        spreadsheet_id = input("Spreadsheet ID: ").strip()
    
    if not spreadsheet_id:
        print("No spreadsheet ID provided. Exiting.")
        exit(1)
    
    print(f"Using spreadsheet ID: {spreadsheet_id}")
    
    # Display spreadsheet info
    display_sheet_info(service, spreadsheet_id)
    
    # Ask which sheet to view (default to Finances)
    print("\nWhich sheet would you like to view?")
    print("  1. Credit Cards")
    print("  2. Finances (default)")
    sheet_choice = input("Enter choice (1 or 2, or press Enter for default): ").strip()
    
    if sheet_choice == "1":
        # Get the first sheet (Credit Cards)
        row_data, values = get_sheet_data(service, spreadsheet_id)
    else:
        # Get the Finances sheet (default)
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        if len(sheets) > 1:
            sheet_name = sheets[1].get('properties', {}).get('title')
            row_data, values = get_sheet_data(service, spreadsheet_id, range_name=sheet_name)
        else:
            print("Finances sheet not found, using first sheet")
            row_data, values = get_sheet_data(service, spreadsheet_id)
    
    if row_data or values:
        # Show more rows to see transaction data - check if we should show more
        print(f"\nFound {len(values)} rows with data")
        show_all = input("Show all rows? (y/n, default n): ").strip().lower()
        max_rows = len(values) if show_all == 'y' else 100
        display_sheet_data(row_data, values, max_rows=max_rows)
        
        print(f"\n{'='*60}")
        print(f"Total rows with data: {len(values)}")
        print(f"{'='*60}\n")
        
        # Calculate and display monthly sums for non-strikethrough rows
        print("\n" + "="*60)
        print("MONTHLY TOTALS (Non-Strikethrough Rows Only)")
        print("="*60)
        
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_name = 'Finances'
        if len(sheets) > 1:
            sheet_name = sheets[1].get('properties', {}).get('title')
        
        monthly_totals = sum_by_month_non_strikethrough(service, spreadsheet_id, sheet_name)
        
        if monthly_totals:
            print("\nMonthly Totals:")
            total_all = 0
            for month in sorted(monthly_totals.keys(), key=lambda x: ['January', 'February', 'March', 'April', 
                                                                       'May', 'June', 'July', 'August', 
                                                                       'September', 'October', 'November', 'December'].index(x) if x in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'] else 999):
                amount = monthly_totals[month]
                total_all += amount
                print(f"  {month:12} ${amount:>12,.2f}")
            print(f"  {'-'*12} {'-'*12}")
            print(f"  {'Total':12} ${total_all:>12,.2f}")
        else:
            print("No monthly totals calculated")
        
        # Ask if user wants to update the "Total Remaining" row
        print("\n" + "="*60)
        update = input("Update the 'Total Remaining' row in the spreadsheet? (y/n, default n): ").strip().lower()
        if update == 'y':
            update_total_remaining_row(service, spreadsheet_id, sheet_name)
    else:
        print("\nNo data found in the spreadsheet.")

