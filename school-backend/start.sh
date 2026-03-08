#!/bin/bash
# Start Django backend - displays real LAN IP address

cd "$(dirname "$0")"
source venv/bin/activate

PORT=${1:-8000}

# Detect LAN IP
LAN_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "127.0.0.1")

echo ""
echo "  Django Backend Server"
echo "  ─────────────────────────────────────"
echo "  Local:    http://127.0.0.1:${PORT}/"
echo "  Network:  http://${LAN_IP}:${PORT}/"
echo "  Admin:    http://${LAN_IP}:${PORT}/admin/"
echo "  API:      http://${LAN_IP}:${PORT}/api/"
echo "  ─────────────────────────────────────"
echo ""

python manage.py runserver 0.0.0.0:${PORT}
