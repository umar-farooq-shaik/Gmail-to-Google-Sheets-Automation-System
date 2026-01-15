# Credentials Directory

Place your OAuth 2.0 credentials file here.

## Setup

1. Download OAuth 2.0 credentials from Google Cloud Console
2. Save the file as `credentials.json` in this directory
3. The file should NOT be committed to version control (already in .gitignore)

## File Structure

```
credentials/
└── credentials.json  # OAuth 2.0 client credentials (DO NOT COMMIT)
```

## Security Warning

⚠️ **NEVER commit `credentials.json` to version control!**

This file contains sensitive OAuth client credentials.

