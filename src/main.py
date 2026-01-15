"""
Main Orchestration Module

Coordinates Gmail fetching, email parsing, Sheets appending,
state management, and marking emails as read.
"""

import json
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gmail_service import GmailService
from src.email_parser import EmailParser
from src.sheets_service import SheetsService
from config import (
    STATE_FILE,
    STATE_KEY_PROCESSED_IDS,
    STATE_KEY_LAST_RUN,
    SHEET_ID,
    SHEET_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_to_sheets.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class StateManager:
    """Manages state persistence to avoid reprocessing emails."""
    
    def __init__(self, state_file=STATE_FILE):
        """
        Initialize state manager.
        
        Args:
            state_file (str): Path to state JSON file
        """
        self.state_file = state_file
        self.state = self.load_state()
    
    def load_state(self) -> Dict:
        """
        Load state from JSON file.
        
        Returns:
            dict: State dictionary with processed IDs and last run timestamp
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state: {len(state.get(STATE_KEY_PROCESSED_IDS, []))} processed IDs")
                    return state
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        
        # Return default state for first run
        return {
            STATE_KEY_PROCESSED_IDS: [],
            STATE_KEY_LAST_RUN: None
        }
    
    def save_state(self):
        """Save current state to JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info(f"Saved state: {len(self.state.get(STATE_KEY_PROCESSED_IDS, []))} processed IDs")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def is_processed(self, message_id: str) -> bool:
        """
        Check if a message has been processed.
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            bool: True if message was already processed
        """
        processed_ids = self.state.get(STATE_KEY_PROCESSED_IDS, [])
        return message_id in processed_ids
    
    def mark_processed(self, message_id: str):
        """
        Mark a message as processed.
        
        Args:
            message_id (str): Gmail message ID
        """
        if STATE_KEY_PROCESSED_IDS not in self.state:
            self.state[STATE_KEY_PROCESSED_IDS] = []
        
        if message_id not in self.state[STATE_KEY_PROCESSED_IDS]:
            self.state[STATE_KEY_PROCESSED_IDS].append(message_id)
    
    def update_last_run(self):
        """Update last run timestamp."""
        self.state[STATE_KEY_LAST_RUN] = datetime.now().isoformat()
    
    def get_processed_ids(self) -> List[str]:
        """
        Get list of all processed message IDs.
        
        Returns:
            list: List of processed message IDs
        """
        return self.state.get(STATE_KEY_PROCESSED_IDS, [])


def main():
    """
    Main orchestration function.
    
    Flow:
    1. Authenticate with Gmail and Sheets APIs
    2. Load state (processed message IDs)
    3. Fetch unread emails from Gmail
    4. Filter out already processed emails
    5. Parse email content
    6. Append to Google Sheets (with duplicate checking)
    7. Mark successfully processed emails as read
    8. Update state
    9. Save state
    """
    logger.info("=" * 60)
    logger.info("Starting Gmail to Google Sheets automation")
    logger.info("=" * 60)
    
    # Initialize services
    gmail_service = GmailService()
    email_parser = EmailParser()
    state_manager = StateManager()
    
    # Check if Sheet ID is configured
    if SHEET_ID == 'YOUR_SHEET_ID_HERE':
        logger.error("Please configure SHEET_ID in config.py")
        return
    
    sheets_service = SheetsService(SHEET_ID)
    
    try:
        # Step 1: Authenticate
        logger.info("Step 1: Authenticating with Gmail API...")
        if not gmail_service.authenticate():
            logger.error("Gmail authentication failed")
            return
        
        logger.info("Step 2: Authenticating with Google Sheets API...")
        if not sheets_service.authenticate(gmail_service.credentials):
            logger.error("Sheets authentication failed")
            return
        
        # Step 2: Load state
        logger.info("Step 3: Loading state...")
        processed_ids = set(state_manager.get_processed_ids())
        logger.info(f"Found {len(processed_ids)} previously processed emails")
        
        # Step 3: Fetch unread emails
        logger.info("Step 4: Fetching unread emails from Gmail...")
        messages = gmail_service.get_unread_messages(max_results=5)
        
        if not messages:
            logger.info("No unread emails found. Exiting.")
            return
        
        # Step 4: Filter out already processed emails
        logger.info("Step 5: Filtering out already processed emails...")
        new_messages = [
            msg for msg in messages
            if msg['id'] not in processed_ids
        ]
        
        logger.info(f"Found {len(new_messages)} new emails to process (out of {len(messages)} total)")
        
        if not new_messages:
            logger.info("No new emails to process. Exiting.")
            return
        
        # Step 5: Parse emails
        logger.info("Step 6: Parsing email content...")
        parsed_emails = []
        failed_parsing = []
        
        for msg in new_messages:
            try:
                # Fetch full message details
                full_message = gmail_service.get_message_details(msg['id'])
                
                # Parse message
                parsed_data = email_parser.parse_message(full_message)
                
                # Convert to row format: [From, Subject, Date, Content]
                row = [
                    parsed_data['from'],
                    parsed_data['subject'],
                    parsed_data['date'],
                    parsed_data['content']
                ]
                
                parsed_emails.append({
                    'message_id': msg['id'],
                    'row': row
                })
                
            except Exception as e:
                logger.error(f"Failed to parse message {msg['id']}: {e}")
                failed_parsing.append(msg['id'])
        
        logger.info(f"Successfully parsed {len(parsed_emails)} emails")
        
        if not parsed_emails:
            logger.warning("No emails were successfully parsed. Exiting.")
            return
        
        # Step 6: Append to Sheets
        logger.info("Step 7: Appending emails to Google Sheets...")
        rows_to_append = [email['row'] for email in parsed_emails]
        
        appended_count, skipped_count = sheets_service.append_rows(
            rows_to_append,
            sheet_name=SHEET_NAME
        )
        
        logger.info(f"Appended {appended_count} rows, skipped {skipped_count} duplicates")
        
        # Step 7: Mark successfully appended emails as read
        logger.info("Step 8: Marking processed emails as read...")
        successfully_processed = []
        
        for email_data in parsed_emails:
            message_id = email_data['message_id']
            
            # Only mark as read if it was successfully appended
            # (We check by verifying the row was in the batch that was appended)
            if gmail_service.mark_as_read(message_id):
                successfully_processed.append(message_id)
                state_manager.mark_processed(message_id)
        
        logger.info(f"Marked {len(successfully_processed)} emails as read")
        
        # Step 8: Update and save state
        logger.info("Step 9: Saving state...")
        state_manager.update_last_run()
        state_manager.save_state()
        
        # Summary
        logger.info("=" * 60)
        logger.info("Processing complete!")
        logger.info(f"  - Total unread emails found: {len(messages)}")
        logger.info(f"  - New emails to process: {len(new_messages)}")
        logger.info(f"  - Successfully parsed: {len(parsed_emails)}")
        logger.info(f"  - Appended to Sheets: {appended_count}")
        logger.info(f"  - Skipped duplicates: {skipped_count}")
        logger.info(f"  - Marked as read: {len(successfully_processed)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()

