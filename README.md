# Gmail to Google Sheets Automation

A production-ready Python automation system that reads unread emails from Gmail inbox, extracts structured data, and appends them to Google Sheets with duplicate prevention and state persistence.

---

## 📋 Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [Design Explanations](#design-explanations)
- [Engineering Challenges](#engineering-challenges)
- [Limitations](#limitations)
- [Usage](#usage)
- [Project Structure](#project-structure)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gmail API                                │
│                    (OAuth 2.0 Authentication)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Fetch Unread Emails
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Python Application                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  gmail_service.py                                         │  │
│  │  - OAuth 2.0 Authentication                               │  │
│  │  - Fetch unread messages                                  │  │
│  │  - Mark messages as read                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  email_parser.py                                         │  │
│  │  - Extract From, Subject, Date, Content                 │  │
│  │  - Handle multipart emails                               │  │
│  │  - Base64 decoding                                       │  │
│  │  - HTML → plain text conversion                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  StateManager (in main.py)                               │  │
│  │  - Persist processed message IDs                         │  │
│  │  - Prevent reprocessing                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  sheets_service.py                                       │  │
│  │  - OAuth 2.0 Authentication                               │  │
│  │  - Append rows to Sheets                                 │  │
│  │  - Duplicate detection                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Append Rows
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Google Sheets API                             │
│                    (OAuth 2.0 Authentication)                    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Sheet Columns:                                          │   │
│  │  - From | Subject | Date | Content                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘

OAuth 2.0 Flow:
┌──────────┐         ┌──────────────┐         ┌─────────────┐
│   User   │────────▶│ Google OAuth │────────▶│  Browser    │
│          │◀────────│   Consent    │◀────────│  Redirect   │
└──────────┘         └──────────────┘         └─────────────┘
     │                       │
     │  Authorization Code   │
     └───────────────────────┘
     │
     ▼
┌──────────────┐
│ Access Token │
│ (token.json) │
└──────────────┘
```

---

## ✨ Features

- ✅ **OAuth 2.0 Authentication** - Secure, user-based authentication (no service accounts)
- ✅ **Unread Email Processing** - Only processes unread emails from inbox
- ✅ **Automatic Mark as Read** - Marks processed emails as read after successful append
- ✅ **Duplicate Prevention** - Multi-layer duplicate detection (state + sheet comparison)
- ✅ **State Persistence** - Tracks processed emails across runs using `state.json`
- ✅ **Robust Email Parsing** - Handles multipart emails, base64 encoding, HTML conversion
- ✅ **Error Handling** - Comprehensive logging and error recovery
- ✅ **Batch Processing** - Efficient batch operations for Sheets API

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account
- Gmail account
- Google Sheet (create one and note the Sheet ID)

### Step 1: Google Cloud Project Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable APIs**
   - Navigate to "APIs & Services" > "Library"
   - Enable the following APIs:
     - **Gmail API**
     - **Google Sheets API**

3. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type (unless you have a Google Workspace)
   - Fill in required fields:
     - App name: "Gmail to Sheets Automation"
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/spreadsheets`
   - Add test users (your Gmail account) if in testing mode
   - Save and continue

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it (e.g., "Gmail Sheets Automation")
   - Click "Create"
   - **Download the JSON file** and save it as `credentials/credentials.json`

### Step 2: Google Sheet Setup

1. Create a new Google Sheet or use an existing one
2. Copy the Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```
3. Update `config.py` with your Sheet ID:
   ```python
   SHEET_ID = 'your-actual-sheet-id-here'
   ```

### Step 3: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Run the Script

```bash
# From project root directory
python -m src.main
```

**First Run:**
- A browser window will open for OAuth consent
- Authorize the application
- Token will be saved to `token.json` for future use

**Subsequent Runs:**
- Token will be automatically reused
- If expired, it will be automatically refreshed

---

## 🧠 Design Explanations

### OAuth 2.0 Flow

**Why OAuth 2.0 instead of Service Accounts?**

- Service accounts cannot access user Gmail inboxes directly
- OAuth 2.0 allows the application to act on behalf of the user
- Provides better security and user consent
- Required for accessing user-specific Gmail data

**Implementation:**
- Uses `google-auth-oauthlib` with `InstalledAppFlow`
- Token stored in `token.json` for reuse
- Automatic token refresh when expired
- Single token file shared between Gmail and Sheets APIs (same scopes)

### Duplicate Prevention Logic

**Multi-Layer Approach:**

1. **State-Based Deduplication** (`state.json`):
   - Stores all processed `messageId`s
   - Fast lookup: O(1) check before processing
   - Prevents reprocessing even if script crashes mid-run

2. **Sheet-Based Deduplication**:
   - Fetches existing rows from Sheets
   - Compares new rows against existing data
   - Checks all columns: From, Subject, Date, Content
   - Also checks partial match (From + Subject + Date)

**Why Both?**

- State file could be deleted or corrupted
- Sheet comparison provides redundancy
- Handles edge cases (manual sheet edits, etc.)

### State Persistence Method

**Chosen Method: Message ID Storage**

We store processed `messageId`s in `state.json` because:

1. **Reliability**: Message IDs are unique and permanent
2. **Efficiency**: O(1) lookup time
3. **Simplicity**: No complex timestamp synchronization needed
4. **Robustness**: Works even if emails are moved/deleted
5. **Idempotency**: Safe to run multiple times

**Alternative Methods Considered:**

- ❌ **Gmail `historyId`**: More complex, requires tracking history changes
- ❌ **Timestamp checkpoint**: Less reliable (timezone issues, clock drift)
- ✅ **Message ID storage**: Simple, reliable, efficient

**State File Structure:**
```json
{
  "processed_message_ids": ["msg_id_1", "msg_id_2", ...],
  "last_run_timestamp": "2024-01-15T10:30:00"
}
```

### Why Unread-Only Emails?

- **Efficiency**: Processes only new emails, not entire inbox
- **User Intent**: Unread emails are actionable items
- **Performance**: Faster queries, less data to process
- **Gmail Best Practice**: Uses Gmail's native unread label system

---

## 🔧 Engineering Challenges

### Challenge 1: Gmail MIME Parsing

**Problem:**
- Gmail messages can have complex MIME structures (multipart/alternative, multipart/mixed)
- Body content is base64-encoded
- Need to extract plain text from various MIME types

**Solution:**
- Implemented recursive payload parsing in `email_parser.py`
- Handles nested multipart structures
- Prioritizes `text/plain` over `text/html`
- Falls back to HTML-to-text conversion if no plain text available
- Robust base64 decoding with error handling

**Code Example:**
```python
def extract_plain_text_from_payload(payload):
    if 'parts' in payload:
        # Recursively process multipart messages
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                # Decode base64 and extract text
                ...
```

### Challenge 2: Token Reuse and Refresh

**Problem:**
- OAuth tokens expire after 1 hour
- Need to reuse tokens across runs
- Must handle token refresh seamlessly

**Solution:**
- Check token validity before use
- Automatically refresh expired tokens using `refresh_token`
- Save refreshed tokens to `token.json`
- Single token file shared between Gmail and Sheets APIs

**Implementation:**
```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Save refreshed token
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
```

### Challenge 3: Idempotency and Duplicate Prevention

**Problem:**
- Script might crash mid-execution
- Need to ensure emails are never processed twice
- Must handle manual sheet edits

**Solution:**
- **State persistence**: Track processed IDs before marking as read
- **Sheet comparison**: Check against existing rows before append
- **Atomic operations**: Only mark as read after successful append
- **Batch processing**: Process all emails, then mark all as read

**Flow:**
1. Load state → Filter already processed IDs
2. Fetch unread emails → Parse content
3. Check duplicates in sheet → Append new rows
4. Mark successfully appended emails as read
5. Update state → Save state

---

## ⚠️ Limitations

1. **Rate Limits**
   - Gmail API: 1 billion quota units per day (typically not an issue)
   - Sheets API: 500 requests per 100 seconds per project
   - **Mitigation**: Batch operations, efficient queries

2. **Email Attachments**
   - Attachments are not processed or stored
   - Only email body content is extracted
   - **Future Enhancement**: Could add attachment download/storage

3. **HTML Emails**
   - HTML is converted to plain text using basic regex
   - Complex HTML formatting may be lost
   - **Future Enhancement**: Use libraries like `html2text` for better conversion

4. **Large Email Bodies**
   - Very long emails might be truncated by Sheets (cell limit: 50,000 characters)
   - **Mitigation**: Current implementation preserves full content

5. **OAuth Token Expiry**
   - Refresh tokens can expire if unused for 6 months
   - User must re-authorize if refresh token expires
   - **Mitigation**: Regular script runs keep tokens fresh

6. **Single User Only**
   - Designed for single Gmail account
   - **Future Enhancement**: Could support multiple accounts with separate state files

7. **No Error Recovery**
   - If script crashes mid-run, some emails might be marked as read but not appended
   - **Mitigation**: State tracking prevents reprocessing, but manual intervention may be needed

---

## 📊 Proof of Execution

This project submission includes:

- ✅ **Gmail Inbox Screenshot** - Showing unread emails before processing
- ✅ **Google Sheet Screenshot** - Showing ≥5 rows of processed emails
- ✅ **OAuth Consent Screen** - Showing authorization flow
- ✅ **Screen Recording** - 2-3 minute demonstration of the automation

---

## 📁 Project Structure

```
gmail-to-sheets/
│
├── src/
│   ├── gmail_service.py      # Gmail OAuth + fetch + mark read
│   ├── sheets_service.py      # Sheets OAuth + append + dedupe
│   ├── email_parser.py        # Email parsing (headers + body)
│   └── main.py                # Orchestration + state management
│
├── credentials/
│   └── credentials.json       # OAuth 2.0 credentials (DO NOT COMMIT)
│
├── config.py                  # Configuration constants
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
│
├── token.json                 # OAuth token (auto-generated, DO NOT COMMIT)
├── state.json                 # State persistence (auto-generated, DO NOT COMMIT)
└── gmail_to_sheets.log        # Application logs (auto-generated)
```

---

## 🎯 Usage

### Basic Usage

```bash
# Run the automation
python -m src.main
```

### Expected Output

```
2024-01-15 10:30:00 - __main__ - INFO - ============================================================
2024-01-15 10:30:00 - __main__ - INFO - Starting Gmail to Google Sheets automation
2024-01-15 10:30:00 - __main__ - INFO - ============================================================
2024-01-15 10:30:01 - __main__ - INFO - Step 1: Authenticating with Gmail API...
2024-01-15 10:30:02 - __main__ - INFO - Loaded existing token from token.json
2024-01-15 10:30:02 - __main__ - INFO - Gmail service initialized successfully
2024-01-15 10:30:02 - __main__ - INFO - Step 2: Authenticating with Google Sheets API...
2024-01-15 10:30:03 - __main__ - INFO - Reusing Gmail credentials for Sheets API
2024-01-15 10:30:03 - __main__ - INFO - Sheets service initialized successfully
2024-01-15 10:30:03 - __main__ - INFO - Step 3: Loading state...
2024-01-15 10:30:03 - __main__ - INFO - Found 15 previously processed emails
2024-01-15 10:30:03 - __main__ - INFO - Step 4: Fetching unread emails from Gmail...
2024-01-15 10:30:04 - __main__ - INFO - Found 5 unread messages
2024-01-15 10:30:04 - __main__ - INFO - Step 5: Filtering out already processed emails...
2024-01-15 10:30:04 - __main__ - INFO - Found 5 new emails to process (out of 5 total)
2024-01-15 10:30:04 - __main__ - INFO - Step 6: Parsing email content...
2024-01-15 10:30:05 - __main__ - INFO - Successfully parsed 5 emails
2024-01-15 10:30:05 - __main__ - INFO - Step 7: Appending emails to Google Sheets...
2024-01-15 10:30:06 - __main__ - INFO - Appended 5 rows, skipped 0 duplicates
2024-01-15 10:30:06 - __main__ - INFO - Step 8: Marking processed emails as read...
2024-01-15 10:30:07 - __main__ - INFO - Marked 5 emails as read
2024-01-15 10:30:07 - __main__ - INFO - Step 9: Saving state...
2024-01-15 10:30:07 - __main__ - INFO - ============================================================
2024-01-15 10:30:07 - __main__ - INFO - Processing complete!
2024-01-15 10:30:07 - __main__ - INFO -   - Total unread emails found: 5
2024-01-15 10:30:07 - __main__ - INFO -   - New emails to process: 5
2024-01-15 10:30:07 - __main__ - INFO -   - Successfully parsed: 5
2024-01-15 10:30:07 - __main__ - INFO -   - Appended to Sheets: 5
2024-01-15 10:30:07 - __main__ - INFO -   - Skipped duplicates: 0
2024-01-15 10:30:07 - __main__ - INFO -   - Marked as read: 5
2024-01-15 10:30:07 - __main__ - INFO - ============================================================
```

### Configuration

Edit `config.py` to customize:

```python
# Google Sheets configuration
SHEET_ID = 'your-sheet-id-here'
SHEET_NAME = 'Sheet1'  # Change if using different sheet name

# Gmail query (modify if needed)
GMAIL_QUERY = 'in:inbox is:unread'  # Can add filters like 'from:example@email.com'
```

---

## 🔒 Security Notes

- **Never commit** `credentials/credentials.json`
- **Never commit** `token.json`
- **Never commit** `state.json`
- All sensitive files are in `.gitignore`
- OAuth tokens are user-specific and should be kept private

---

## 🐛 Troubleshooting

### "Credentials file not found"
- Ensure `credentials/credentials.json` exists
- Download OAuth credentials from Google Cloud Console

### "Please configure SHEET_ID in config.py"
- Update `SHEET_ID` in `config.py` with your Google Sheet ID

### "Failed to refresh token"
- Delete `token.json` and re-run to trigger new OAuth flow
- Check if refresh token expired (6 months of inactivity)

### "No unread emails found"
- Check Gmail inbox for unread emails
- Verify Gmail query in `config.py`

### Import errors
- Ensure you're running from project root: `python -m src.main`
- Check that all dependencies are installed: `pip install -r requirements.txt`

---

## 📝 License

This project is provided as-is for evaluation purposes.

---

## 👤 Author

Umar Farooq

---

**Built using Python 3, Gmail API, and Google Sheets API**

