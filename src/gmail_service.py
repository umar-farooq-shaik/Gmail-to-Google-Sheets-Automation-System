"""
Gmail Service Module

Handles OAuth 2.0 authentication with Gmail API,
fetches unread emails from inbox, and marks them as read.
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

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, GMAIL_SCOPE, GMAIL_QUERY

logger = logging.getLogger(__name__)


class GmailService:
    """Service class for Gmail API operations."""
    
    def __init__(self):
        """Initialize Gmail service with OAuth authentication."""
        self.service = None
        self.credentials = None
    
    def authenticate(self):
        """
        Authenticate with Gmail API using OAuth 2.0.
        
        Reuses existing token if valid, otherwise triggers OAuth flow.
        Stores token in token.json for future use.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
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
                # Refresh expired token
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired token")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                # Start OAuth flow
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
        
        # Build Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service initialized successfully")
            return True
        except HttpError as error:
            logger.error(f"Failed to build Gmail service: {error}")
            return False
    
    def get_unread_messages(self, max_results=5):
        """
        Fetch unread messages from Gmail inbox.
        
        Args:
            max_results (int): Maximum number of messages to fetch per page
            
        Returns:
            list: List of message objects with 'id' and 'threadId'
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated. Call authenticate() first.")
        
        try:
            # Query for unread emails in inbox
            results = self.service.users().messages().list(
                userId='me',
                q=GMAIL_QUERY,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread messages")
            
            return messages
            
        except HttpError as error:
            logger.error(f"Failed to fetch messages: {error}")
            raise
    
    def get_message_details(self, message_id):
        """
        Fetch full message details including headers and body.
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            dict: Full message object with payload
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated. Call authenticate() first.")
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return message
            
        except HttpError as error:
            logger.error(f"Failed to fetch message {message_id}: {error}")
            raise
    
    def mark_as_read(self, message_id):
        """
        Mark a message as read by removing the UNREAD label.
        
        Args:
            message_id (str): Gmail message ID to mark as read
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated. Call authenticate() first.")
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.debug(f"Marked message {message_id} as read")
            return True
            
        except HttpError as error:
            logger.error(f"Failed to mark message {message_id} as read: {error}")
            return False
    
    def mark_multiple_as_read(self, message_ids):
        """
        Mark multiple messages as read in batch.
        
        Args:
            message_ids (list): List of Gmail message IDs
            
        Returns:
            int: Number of successfully marked messages
        """
        success_count = 0
        for msg_id in message_ids:
            if self.mark_as_read(msg_id):
                success_count += 1
        
        logger.info(f"Marked {success_count}/{len(message_ids)} messages as read")
        return success_count

