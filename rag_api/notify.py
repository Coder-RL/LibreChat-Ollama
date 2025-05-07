#!/usr/bin/env python3
"""
Notification Script for RAG API Security Alerts

This script provides email and Slack notification capabilities for security alerts
from the RAG API. It can be used to send notifications when security events occur,
such as multiple failed authentication attempts or rate limit violations.

Usage:
    python notify.py email --to recipient@example.com --subject "Security Alert" --message "Alert details"
    python notify.py slack --webhook https://hooks.slack.com/services/XXX/YYY/ZZZ --channel "#security" --message "Alert details"
"""

import os
import sys
import json
import argparse
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email(to, subject, message, from_email=None, smtp_server=None, smtp_port=None, 
               smtp_user=None, smtp_password=None):
    """
    Send an email notification.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        message (str): Email message
        from_email (str, optional): Sender email address
        smtp_server (str, optional): SMTP server
        smtp_port (int, optional): SMTP port
        smtp_user (str, optional): SMTP username
        smtp_password (str, optional): SMTP password
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get email settings from environment variables if not provided
    from_email = from_email or os.environ.get("SMTP_FROM", "rag-api-alerts@example.com")
    smtp_server = smtp_server or os.environ.get("SMTP_SERVER", "localhost")
    smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "25"))
    smtp_user = smtp_user or os.environ.get("SMTP_USER")
    smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
    
    # Create message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to
    msg["Subject"] = subject
    
    # Add timestamp to message
    full_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    msg.attach(MIMEText(full_message, "plain"))
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        
        # Use TLS if available
        if smtp_user and smtp_password:
            server.starttls()
            server.login(smtp_user, smtp_password)
        
        # Send email
        server.sendmail(from_email, to, msg.as_string())
        server.quit()
        
        print(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def send_slack(webhook_url, message, channel=None, username=None):
    """
    Send a Slack notification.
    
    Args:
        webhook_url (str): Slack webhook URL
        message (str): Message to send
        channel (str, optional): Slack channel
        username (str, optional): Bot username
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    # Get Slack settings from environment variables if not provided
    webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK")
    channel = channel or os.environ.get("SLACK_CHANNEL", "#security-alerts")
    username = username or os.environ.get("SLACK_USERNAME", "RAG API Security Bot")
    
    if not webhook_url:
        print("❌ Slack webhook URL is required")
        return False
    
    # Create payload
    payload = {
        "text": f"🚨 *SECURITY ALERT*\n{message}",
        "username": username
    }
    
    if channel:
        payload["channel"] = channel
    
    try:
        # Send request to Slack
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Slack message sent to {channel}")
            return True
        else:
            print(f"❌ Failed to send Slack message: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send Slack message: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Send notifications for RAG API security alerts")
    subparsers = parser.add_subparsers(dest="command", help="Notification method")
    
    # Email command
    email_parser = subparsers.add_parser("email", help="Send email notification")
    email_parser.add_argument("--to", required=True, help="Recipient email address")
    email_parser.add_argument("--subject", required=True, help="Email subject")
    email_parser.add_argument("--message", required=True, help="Email message")
    email_parser.add_argument("--from", dest="from_email", help="Sender email address")
    email_parser.add_argument("--smtp-server", help="SMTP server")
    email_parser.add_argument("--smtp-port", type=int, help="SMTP port")
    email_parser.add_argument("--smtp-user", help="SMTP username")
    email_parser.add_argument("--smtp-password", help="SMTP password")
    
    # Slack command
    slack_parser = subparsers.add_parser("slack", help="Send Slack notification")
    slack_parser.add_argument("--webhook", help="Slack webhook URL")
    slack_parser.add_argument("--channel", help="Slack channel")
    slack_parser.add_argument("--message", required=True, help="Slack message")
    slack_parser.add_argument("--username", help="Bot username")
    
    args = parser.parse_args()
    
    if args.command == "email":
        send_email(
            args.to,
            args.subject,
            args.message,
            args.from_email,
            args.smtp_server,
            args.smtp_port,
            args.smtp_user,
            args.smtp_password
        )
    elif args.command == "slack":
        send_slack(
            args.webhook,
            args.message,
            args.channel,
            args.username
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
