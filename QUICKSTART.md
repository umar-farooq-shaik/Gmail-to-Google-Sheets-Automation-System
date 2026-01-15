# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Credentials
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create OAuth 2.0 credentials (Desktop app)
- Download and save as `credentials/credentials.json`

### 3. Configure Sheet ID
Edit `config.py`:
```python
SHEET_ID = 'your-actual-sheet-id-here'
```

### 4. Run the Script
```bash
python -m src.main
```

### 5. Authorize (First Run Only)
- Browser will open for OAuth consent
- Authorize the application
- Token saved automatically

**Done!** Your unread emails will now be synced to Google Sheets.

---

## 📋 Checklist

- [ ] Python 3.7+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Gmail API enabled in Google Cloud Console
- [ ] Google Sheets API enabled in Google Cloud Console
- [ ] OAuth consent screen configured
- [ ] `credentials/credentials.json` downloaded
- [ ] `SHEET_ID` configured in `config.py`
- [ ] Google Sheet created and accessible

---

## 🆘 Need Help?

See [README.md](README.md) for detailed setup instructions and troubleshooting.

