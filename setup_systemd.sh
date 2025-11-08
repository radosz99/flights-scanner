#!/bin/bash
#
# Setup systemd timer to run flight scanner every 8 hours
#
# This creates a systemd service and timer that runs more reliably than cron
# Requires root/sudo access to install
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIGGER_SCRIPT="$SCRIPT_DIR/trigger_scan.py"
SERVICE_NAME="flight-scanner"
USER=$(whoami)

echo "========================================"
echo "Flight Scanner - Systemd Timer Setup"
echo "========================================"
echo ""
echo "This will create a systemd service and timer"
echo "to run scans every 8 hours"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠ This script requires sudo/root access"
    echo "Run with: sudo $0"
    exit 1
fi

# Make trigger script executable
chmod +x "$TRIGGER_SCRIPT"

# Create systemd service file
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Flight Scanner - Trigger Scan
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $TRIGGER_SCRIPT
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="API_URL=http://localhost:8000"
Environment="TRIP_DURATION_DAYS=7"
Environment="SCAN_UNTIL_DAYS=365"

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer file
cat > /etc/systemd/system/${SERVICE_NAME}.timer <<EOF
[Unit]
Description=Flight Scanner - Run every 8 hours
Requires=${SERVICE_NAME}.service

[Timer]
# Run every 8 hours
OnCalendar=*-*-* 00,08,16:00:00
# Run 5 minutes after boot if a scheduled run was missed
OnBootSec=5min
# Allow timer to drift up to 30 minutes for better resource distribution
AccuracySec=30min
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "✓ Created service file: /etc/systemd/system/${SERVICE_NAME}.service"
echo "✓ Created timer file: /etc/systemd/system/${SERVICE_NAME}.timer"
echo ""

# Reload systemd daemon
systemctl daemon-reload
echo "✓ Reloaded systemd daemon"
echo ""

# Enable and start timer
systemctl enable ${SERVICE_NAME}.timer
systemctl start ${SERVICE_NAME}.timer

echo "✓ Enabled and started timer"
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "The scanner will run at: 00:00, 08:00, 16:00 daily"
echo ""
echo "Useful commands:"
echo "  # Check timer status"
echo "  systemctl status ${SERVICE_NAME}.timer"
echo ""
echo "  # List all timers"
echo "  systemctl list-timers"
echo ""
echo "  # View logs"
echo "  journalctl -u ${SERVICE_NAME}.service -f"
echo ""
echo "  # Run manually now"
echo "  systemctl start ${SERVICE_NAME}.service"
echo ""
echo "  # Disable timer"
echo "  systemctl stop ${SERVICE_NAME}.timer"
echo "  systemctl disable ${SERVICE_NAME}.timer"
echo ""
echo "========================================"
