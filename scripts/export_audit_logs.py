#!/usr/bin/env python3
"""
Export audit logs to OpenSearch.

This script is designed to be run as a cron job to automatically export
audit logs to OpenSearch on a regular schedule.
"""
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the OpenSearch uploader
from audit_opensearch_uploader import upload_logs, parse_log_line

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/audit_export.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

def get_audit_logs_since(log_file: str, since: datetime) -> List[Dict[str, Any]]:
    """
    Get audit logs since a specific time.
    
    Args:
        log_file: The path to the audit log file
        since: The datetime to get logs since
        
    Returns:
        List[Dict[str, Any]]: The parsed log entries
    """
    if not os.path.exists(log_file):
        logger.error(f"Log file {log_file} not found")
        return []
    
    logs = []
    with open(log_file, "r") as f:
        for line in f:
            doc = parse_log_line(line)
            if doc:
                try:
                    # Parse the timestamp
                    timestamp = datetime.fromisoformat(doc['timestamp'])
                    # Check if the log is newer than the since time
                    if timestamp >= since:
                        logs.append(doc)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing timestamp: {e}")
    
    return logs

def export_logs_to_opensearch(since: Optional[datetime] = None) -> int:
    """
    Export logs to OpenSearch.
    
    Args:
        since: The datetime to get logs since (default: 24 hours ago)
        
    Returns:
        int: The number of logs exported
    """
    # Default to 24 hours ago if no since time is provided
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(days=1)
    
    logger.info(f"Exporting logs since {since.isoformat()}")
    
    # Get the logs
    log_file = "logs/audit.log"
    logs = get_audit_logs_since(log_file, since)
    
    if not logs:
        logger.info("No logs found to export")
        return 0
    
    logger.info(f"Found {len(logs)} logs to export")
    
    # Upload the logs to OpenSearch
    try:
        uploaded = upload_logs(log_file=log_file)
        logger.info(f"Exported {uploaded} logs to OpenSearch")
        return uploaded
    except Exception as e:
        logger.error(f"Error exporting logs to OpenSearch: {e}")
        return 0

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Export logs from the last 24 hours
    since = datetime.now(timezone.utc) - timedelta(days=1)
    exported = export_logs_to_opensearch(since)
    
    print(f"Exported {exported} logs to OpenSearch")
