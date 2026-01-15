"""
Email Parser Module

Extracts structured data from Gmail message objects:
- From (sender email)
- Subject
- Date (RFC3339 → readable format)
- Content (plain-text body)
"""

import base64
import email
from email.header import decode_header
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class EmailParser:
    """Parser for extracting structured data from Gmail messages."""
    
    @staticmethod
    def decode_mime_words(s):
        """
        Decode MIME encoded words in email headers.
        
        Args:
            s (str): MIME encoded string
            
        Returns:
            str: Decoded string
        """
        decoded_parts = decode_header(s)
        decoded_string = ''
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string
    
    @staticmethod
    def get_header_value(headers, name):
        """
        Extract header value from Gmail message headers.
        
        Args:
            headers (list): List of header dicts with 'name' and 'value'
            name (str): Header name to extract
            
        Returns:
            str: Header value or empty string
        """
        for header in headers:
            if header['name'].lower() == name.lower():
                return EmailParser.decode_mime_words(header['value'])
        return ''
    
    @staticmethod
    def extract_plain_text_from_payload(payload):
        """
        Extract plain text from email payload.
        Handles multipart messages and base64 encoding.
        
        Args:
            payload (dict): Gmail message payload
            
        Returns:
            str: Plain text content
        """
        body = ''
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        try:
                            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        except Exception as e:
                            logger.warning(f"Failed to decode part: {e}")
                
                elif mime_type == 'text/html' and not body:
                    # Fallback to HTML if no plain text found
                    data = part.get('body', {}).get('data', '')
                    if data:
                        try:
                            html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            # Simple HTML tag removal (basic fallback)
                            body = EmailParser.html_to_text(html_content)
                        except Exception as e:
                            logger.warning(f"Failed to decode HTML part: {e}")
                
                # Recursively check nested parts
                if 'parts' in part:
                    nested_body = EmailParser.extract_plain_text_from_payload(part)
                    if nested_body and not body:
                        body = nested_body
        
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            data = payload.get('body', {}).get('data', '')
            
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    
                    if mime_type == 'text/plain':
                        body = decoded
                    elif mime_type == 'text/html':
                        # Convert HTML to text
                        body = EmailParser.html_to_text(decoded)
                    else:
                        body = decoded
                        
                except Exception as e:
                    logger.warning(f"Failed to decode body: {e}")
        
        return body.strip()
    
    @staticmethod
    def html_to_text(html_content):
        """
        Convert HTML content to plain text (basic implementation).
        Removes HTML tags and decodes HTML entities.
        
        Args:
            html_content (str): HTML string
            
        Returns:
            str: Plain text content
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Decode numeric entities (basic)
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def format_date(timestamp_ms):
        """
        Convert Gmail internal date (milliseconds since epoch) to readable format.
        
        Args:
            timestamp_ms (int): Milliseconds since epoch
            
        Returns:
            str: Formatted date string (RFC3339-like readable format)
        """
        try:
            timestamp_s = timestamp_ms / 1000
            dt = datetime.fromtimestamp(timestamp_s)
            # Format: YYYY-MM-DD HH:MM:SS
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.warning(f"Failed to format date {timestamp_ms}: {e}")
            return str(timestamp_ms)
    
    @staticmethod
    def parse_message(message):
        """
        Parse Gmail message object and extract structured data.
        
        Args:
            message (dict): Full Gmail message object
            
        Returns:
            dict: Parsed email data with keys: 'from', 'subject', 'date', 'content'
        """
        try:
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            # Extract headers
            from_email = EmailParser.get_header_value(headers, 'From')
            subject = EmailParser.get_header_value(headers, 'Subject')
            
            # Extract date
            internal_date = message.get('internalDate')
            if internal_date:
                date_str = EmailParser.format_date(int(internal_date))
            else:
                date_header = EmailParser.get_header_value(headers, 'Date')
                date_str = date_header if date_header else 'Unknown'
            
            # Extract body content
            content = EmailParser.extract_plain_text_from_payload(payload)
            
            # Clean up from field (extract email if it contains name)
            # Example: "John Doe <john@example.com>" -> "john@example.com"
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_email)
            if email_match:
                from_email = email_match.group(0)
            
            parsed_data = {
                'from': from_email,
                'subject': subject,
                'date': date_str,
                'content': content
            }
            
            logger.debug(f"Parsed message: {subject[:50]}...")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            raise

