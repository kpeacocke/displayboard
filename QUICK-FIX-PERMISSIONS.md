# Quick Fix for NeoPixel Permission Denied

## On Your Raspberry Pi RIGHT NOW:

```bash
# 1. Navigate to your project
cd /path/to/displayboard

# 2. Copy the udev rules file
sudo cp deployment/99-neopixel.rules /etc/udev/rules.d/
sudo chmod 644 /etc/udev/rules.d/99-neopixel.rules

# 3. Add yourself to gpio and video groups
sudo usermod -a -G gpio,video $USER

# 4. Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# 5. IMPORTANT: Log out and log back in
# (SSH users: exit and reconnect)
exit

# --- After logging back in ---

# 6. Verify groups
groups
# Should show: pi gpio video ...

# 7. Verify /dev/mem permissions
ls -l /dev/mem
# Should show: crw-rw---- 1 root gpio ...

# 8. Test without sudo
cd /path/to/displayboard
poetry run python -m displayboard.main --no-video --no-sounds --no-bell -d

# 9. If it works, run the full app
poetry run python -m displayboard.main -d
```

## Or Use the Automated Script:

```bash
cd /path/to/displayboard
sudo bash deployment/setup-permissions.sh
# Then log out and back in
```

## Quick Test Command:

After setting permissions, test NeoPixels only:
```bash
poetry run python -m displayboard.main --no-video --no-sounds --no-bell -d
```

## If You Still Get Permission Errors:

1. ✅ Did you log out and back in? (Required!)
2. ✅ Check: `groups` shows `gpio` and `video`
3. ✅ Check: `ls -l /dev/mem` shows group `gpio`
4. 🔄 Try rebooting: `sudo reboot`

## Temporary Workaround (if you can't log out now):

```bash
# This works but requires sudo each time
sudo $(poetry env info --path)/bin/python -m displayboard.main -d
```
