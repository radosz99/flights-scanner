#!/bin/bash
#
# Setup cron job to run flight scanner every 8 hours
#
# This script adds a cron job that will trigger a scan every 8 hours:
# - At 00:00 (midnight)
# - At 08:00 (8am)
# - At 16:00 (4pm)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIGGER_SCRIPT="$SCRIPT_DIR/trigger_scan.py"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Make trigger script executable
chmod +x "$TRIGGER_SCRIPT"

# Cron job command
# Runs at 00:00, 08:00, and 16:00 every day
CRON_SCHEDULE="0 0,8,16 * * *"
CRON_COMMAND="cd $SCRIPT_DIR && /usr/bin/python3 $TRIGGER_SCRIPT >> $LOG_DIR/scan_trigger.log 2>&1"
CRON_JOB="$CRON_SCHEDULE $CRON_COMMAND"

echo "========================================"
echo "Flight Scanner - Cron Setup"
echo "========================================"
echo ""
echo "This will add a cron job to run scans every 8 hours"
echo "Schedule: 00:00, 08:00, 16:00 daily"
echo ""
echo "Cron job:"
echo "$CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -F "$TRIGGER_SCRIPT" > /dev/null; then
    echo "⚠ Cron job already exists!"
    echo ""
    echo "Current crontab entries for trigger_scan.py:"
    crontab -l | grep -F "$TRIGGER_SCRIPT"
    echo ""
    read -p "Do you want to remove old entries and add new one? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entries
        crontab -l | grep -v -F "$TRIGGER_SCRIPT" | crontab -
        echo "✓ Removed old cron entries"
    else
        echo "Exiting without changes"
        exit 0
    fi
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✓ Cron job added successfully!"
echo ""
echo "You can verify with: crontab -l"
echo "View logs at: $LOG_DIR/scan_trigger.log"
echo ""
echo "To remove the cron job later, run:"
echo "  crontab -e"
echo "  # Then delete the line with '$TRIGGER_SCRIPT'"
echo ""
echo "========================================"
