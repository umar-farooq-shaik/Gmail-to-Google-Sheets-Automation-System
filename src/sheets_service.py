"""
Google Sheets Service Module

Handles OAuth 2.0 authentication with Google Sheets API,
appends rows to sheets, and prevents duplicates.
"""

import os
import sys
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, SHEETS_SCOPE

logger = logging.getLogger(__name__)


class SheetsService:
    """Service class for Google Sheets API operations."""
    
    def __init__(self, sheet_id):
        """
        Initialize Sheets service.
        
        Args:
            sheet_id (str): Google Sheet ID
        """
        self.sheet_id = sheet_id
        self.service = None
        self.credentials = None
    
    def authenticate(self, gmail_credentials=None):
        """
        Authenticate with Google Sheets API using OAuth 2.0.
        
        Can reuse Gmail credentials if they have Sheets scope.
        Otherwise, loads or creates new token.
        
        Args:
            gmail_credentials (Credentials): Optional Gmail credentials to reuse
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Try to reuse Gmail credentials if available
        if gmail_credentials and gmail_credentials.valid:
            # Check if credentials have Sheets scope
            if any('spreadsheets' in scope for scope in gmail_credentials.scopes):
                self.credentials = gmail_credentials
                logger.info("Reusing Gmail credentials for Sheets API")
            else:
                logger.warning("Gmail credentials don't have Sheets scope, creating new token")
                gmail_credentials = None
        
        if not self.credentials:
            creds = None
            
            # Load existing token if available
            if os.path.exists(TOKEN_FILE):
                try:
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                    logger.info("Loaded existing token from token.json")
                except Exception as e:
                    logger.warning(f"Failed to load token: {e}")
            
            # If no valid credentials, trigger OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Refreshed expired token")
                    except Exception as e:
                        logger.error(f"Failed to refresh token: {e}")
                        creds = None
                
                if not creds:
                    if not os.path.exists(CREDENTIALS_FILE):
                        raise FileNotFoundError(
                            f"Credentials file not found: {CREDENTIALS_FILE}\n"
                            "Please download OAuth 2.0 credentials from Google Cloud Console."
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Completed OAuth flow")
                
                # Save token for future use
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"Saved token to {TOKEN_FILE}")
            
            self.credentials = creds
        
        # Build Sheets service
        try:
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Sheets service initialized successfully")
            return True
        except HttpError as error:
            logger.error(f"Failed to build Sheets service: {error}")
            return False
    
    def ensure_header_row(self, sheet_name='Sheet1'):
        """
        Ensure header row exists in the sheet.
        Creates header row if sheet is empty.
        
        Args:
            sheet_name (str): Name of the sheet
            
        Returns:
            bool: True if header row exists or was created
        """
        if not self.service:
            raise RuntimeError("Sheets service not authenticated. Call authenticate() first.")
        
        try:
            from config import HEADER_ROW
            
            # Check if sheet has any data
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A1:D1"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                # Sheet is empty, add header row
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"{sheet_name}!A1:D1",
                    valueInputOption='RAW',
                    body={'values': [HEADER_ROW]}
                ).execute()
                logger.info(f"Created header row in {sheet_name}")
            else:
                logger.debug(f"Header row already exists in {sheet_name}")
            
            return True
            
        except HttpError as error:
            logger.error(f"Failed to ensure header row: {error}")
            return False
    
    def get_existing_rows(self, sheet_name='Sheet1', max_rows=10000):
        """
        Fetch existing rows from sheet to check for duplicates.
        
        Args:
            sheet_name (str): Name of the sheet
            max_rows (int): Maximum number of rows to fetch
            
        Returns:
            list: List of existing rows (excluding header)
        """
        if not self.service:
            raise RuntimeError("Sheets service not authenticated. Call authenticate() first.")
        
        try:
            # Fetch rows (skip header)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A2:D{max_rows + 1}"
            ).execute()
            
            values = result.get('values', [])
            logger.debug(f"Fetched {len(values)} existing rows from sheet")
            
            return values
            
        except HttpError as error:
            logger.error(f"Failed to fetch existing rows: {error}")
            return []
    
    def is_duplicate(self, new_row, existing_rows):
        """
        Check if a row already exists in the sheet.
        Compares all columns (From, Subject, Date, Content).
        
        Args:
            new_row (list): New row to check [from, subject, date, content]
            existing_rows (list): List of existing rows
            
        Returns:
            bool: True if duplicate found, False otherwise
        """
        # Normalize row for comparison (handle missing columns)
        normalized_new = [str(cell).strip().lower() if cell else '' for cell in new_row]
        
        for existing_row in existing_rows:
            # Normalize existing row
            normalized_existing = [str(cell).strip().lower() if cell else '' for cell in existing_row]
            
            # Compare all columns
            if len(normalized_new) == len(normalized_existing):
                if normalized_new == normalized_existing:
                    return True
            
            # Also check if From + Subject + Date match (more lenient check)
            if (len(normalized_new) >= 3 and len(normalized_existing) >= 3):
                if (normalized_new[0] == normalized_existing[0] and  # From
                    normalized_new[1] == normalized_existing[1] and  # Subject
                    normalized_new[2] == normalized_existing[2]):   # Date
                    return True
        
        return False
    
    def append_rows(self, rows, sheet_name='Sheet1'):
        """
        Append rows to Google Sheet, skipping duplicates.
        
        Args:
            rows (list): List of rows, each row is [from, subject, date, content]
            sheet_name (str): Name of the sheet
            
        Returns:
            tuple: (appended_count, skipped_count) - number of rows appended and skipped
        """
        if not self.service:
            raise RuntimeError("Sheets service not authenticated. Call authenticate() first.")
        
        if not rows:
            logger.info("No rows to append")
            return (0, 0)
        
        # Ensure header row exists
        self.ensure_header_row(sheet_name)
        
        # Get existing rows for duplicate checking
        existing_rows = self.get_existing_rows(sheet_name)
        
        # Filter out duplicates
        new_rows = []
        skipped_count = 0
        
        for row in rows:
            if self.is_duplicate(row, existing_rows):
                skipped_count += 1
                logger.debug(f"Skipped duplicate row: {row[1][:50]}...")
            else:
                new_rows.append(row)
                # Add to existing_rows to prevent duplicates within this batch
                existing_rows.append(row)
        
        if not new_rows:
            logger.info(f"All {len(rows)} rows were duplicates, nothing to append")
            return (0, skipped_count)
        
        # Batch append new rows
        try:
            body = {
                'values': new_rows
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A:D",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            appended_count = result.get('updates', {}).get('updatedRows', 0)
            logger.info(f"Appended {appended_count} rows, skipped {skipped_count} duplicates")
            
            return (appended_count, skipped_count)
            
        except HttpError as error:
            logger.error(f"Failed to append rows: {error}")
            raise

