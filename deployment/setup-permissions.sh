#!/bin/bash
# Setup GPIO and NeoPixel permissions for non-root access

set -e

echo "🔧 Setting up GPIO and NeoPixel permissions..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "✅ Running with sudo privileges"
else
    echo "❌ This script must be run with sudo"
    echo "   Usage: sudo bash setup-permissions.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"

echo "📦 Installing udev rules for GPIO/NeoPixel access..."

# Copy udev rules to system directory
cp 99-neopixel.rules /etc/udev/rules.d/
chmod 644 /etc/udev/rules.d/99-neopixel.rules

echo "👥 Adding user '$ACTUAL_USER' to required groups..."

# Add user to gpio group (for GPIO access)
usermod -a -G gpio "$ACTUAL_USER"

# Add user to video group (sometimes needed for DMA)
usermod -a -G video "$ACTUAL_USER"

# Add user to spi group if it exists (for SPI-based LED strips)
if getent group spi > /dev/null 2>&1; then
    usermod -a -G spi "$ACTUAL_USER"
fi

echo "🔄 Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger

echo ""
echo "✅ Permissions setup complete!"
echo ""
echo "⚠️  IMPORTANT: You must log out and log back in for group changes to take effect."
echo ""
echo "To verify groups, run: groups"
echo "You should see: gpio video (and possibly spi)"
echo ""
echo "After logging back in, test with:"
echo "  cd /opt/displayboard/current"
echo "  poetry run python -m displayboard.main --no-video -d"
echo ""
