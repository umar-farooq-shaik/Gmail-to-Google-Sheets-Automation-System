"""
Configuration file for Gmail to Google Sheets automation.

Contains constants, OAuth scopes, and configuration settings.
"""

# Google API Scopes
GMAIL_SCOPE = ['https://www.googleapis.com/auth/gmail.modify']
SHEETS_SCOPE = ['https://www.googleapis.com/auth/spreadsheets']

# Combined scopes for OAuth
SCOPES = GMAIL_SCOPE + SHEETS_SCOPE

# File paths
CREDENTIALS_FILE = 'credentials/credentials.json'
TOKEN_FILE = 'token.json'
STATE_FILE = 'state.json'

# Google Sheets configuration
# TODO: Replace with your actual Google Sheet ID
SHEET_ID = '1p0augs0BT5a0inFRrXkPc_rAF1a7fyL6YtZ2ux7SonA'

# Sheet configuration
SHEET_NAME = 'Sheet1'  # Default sheet name
HEADER_ROW = ['From', 'Subject', 'Date', 'Content']

# Gmail query configuration
GMAIL_QUERY = 'in:inbox is:unread'

# State management
# Using messageId storage for state persistence
# This ensures we never reprocess the same email
STATE_KEY_PROCESSED_IDS = 'processed_message_ids'
STATE_KEY_LAST_RUN = 'last_run_timestamp'

