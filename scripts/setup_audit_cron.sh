#!/bin/bash

# This script sets up a cron job to export audit logs to OpenSearch every night at 1:00 AM

# Get the absolute path to the project directory
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)

# Get the path to the Python executable in the virtual environment
if [ -d "$PROJECT_DIR/.venv" ]; then
    PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
else
    PYTHON_PATH=$(which python3)
fi

# Create the cron job command
CRON_CMD="0 1 * * * $PYTHON_PATH $PROJECT_DIR/scripts/export_audit_logs.py >> $PROJECT_DIR/logs/audit_export.log 2>&1"

# Check if the cron job already exists
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "$PROJECT_DIR/scripts/export_audit_logs.py")

if [ -n "$EXISTING_CRON" ]; then
    echo "Cron job already exists:"
    echo "$EXISTING_CRON"
    echo "No changes made."
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Cron job added:"
    echo "$CRON_CMD"
    echo "Audit logs will be exported to OpenSearch every night at 1:00 AM."
fi

# Verify the cron job was added
echo "Current crontab:"
crontab -l
