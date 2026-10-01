# NeoPixel Permissions Setup

This directory contains files to enable NeoPixel LED control without requiring root access.

## Quick Setup (On Raspberry Pi)

```bash
# 1. Copy files to your Pi (if deploying from another machine)
scp 99-neopixel.rules setup-permissions.sh pi@raspberrypi.local:~/

# 2. Run the permission setup script
sudo bash setup-permissions.sh

# 3. Log out and log back in for group changes to take effect

# 4. Verify you're in the right groups
groups
# Should output: pi gpio video ...

# 5. Test NeoPixel without sudo
cd /path/to/displayboard
poetry run python -m displayboard.main --no-video --no-sounds --no-bell -d
```

## What This Does

The setup script:
1. **Installs udev rules** (`99-neopixel.rules`) to `/etc/udev/rules.d/`
   - Grants `gpio` group access to `/dev/mem` (required for DMA)
   - Grants access to GPIO, SPI, and PWM devices
   
2. **Adds your user to required groups:**
   - `gpio` - for GPIO and /dev/mem access
   - `video` - for DMA operations
   - `spi` - for SPI-based LED strips (if group exists)

3. **Reloads udev rules** to apply changes immediately

## Manual Installation

If you prefer to install manually:

```bash
# 1. Copy udev rules
sudo cp 99-neopixel.rules /etc/udev/rules.d/
sudo chmod 644 /etc/udev/rules.d/99-neopixel.rules

# 2. Add user to groups
sudo usermod -a -G gpio,video $USER

# 3. Reload udev
sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Log out and back in
```

## Verification

After logging back in, verify the setup:

```bash
# Check group membership
groups
# Should show: gpio video

# Check /dev/mem permissions
ls -l /dev/mem
# Should show: crw-rw---- 1 root gpio 1, 1 ... /dev/mem

# Check udev rules
cat /etc/udev/rules.d/99-neopixel.rules

# Test NeoPixel without sudo
cd /opt/displayboard/current
poetry run python -m displayboard.main --no-video --no-sounds --no-bell -d
```

## Troubleshooting

### Still getting "permission denied" errors?

1. **Verify you logged out and back in** - Group changes only take effect after re-login
2. **Check groups:** `groups` should show `gpio` and `video`
3. **Check /dev/mem permissions:** `ls -l /dev/mem` should show group `gpio`
4. **Reboot the Pi** if udev rules didn't apply: `sudo reboot`

### Alternative: Run with sudo (not recommended)

```bash
sudo $(poetry env info --path)/bin/python -m displayboard.main
```

This works but:
- ❌ Runs with elevated privileges (security risk)
- ❌ Service won't work properly
- ❌ File permissions may get messed up

## Security Note

These permissions are safe because:
- Only members of the `gpio` group get access
- Standard users are not in this group by default
- You explicitly add trusted users to the group
- This is the standard approach for GPIO access on Raspberry Pi

## See Also

- [rpi_ws281x library documentation](https://github.com/jgarff/rpi_ws281x)
- [Raspberry Pi GPIO permissions](https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header)
