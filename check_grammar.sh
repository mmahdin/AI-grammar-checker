#!/bin/bash
# Grammar checker script - place this in /usr/bin/check_grammar.sh
# Make it executable: chmod +x /usr/bin/check_grammar.sh
# Bind to Ctrl+R using your desktop environment's keyboard settings

# Configuration
API_URL="http://127.0.0.1:8765/check"

# Get clipboard content using xclip (install with: sudo apt-get install xclip)
# Alternative tools: xsel, wl-paste (for Wayland)
CLIPBOARD_TEXT=$(xclip -o -selection clipboard 2>/dev/null)

# Fallback to xsel if xclip is not available
if [ -z "$CLIPBOARD_TEXT" ]; then
    CLIPBOARD_TEXT=$(xsel --clipboard --output 2>/dev/null)
fi

# Check if clipboard is empty
if [ -z "$CLIPBOARD_TEXT" ]; then
    notify-send "Grammar Checker" "Clipboard is empty!" -u critical
    exit 1
fi

# Escape the text for JSON
ESCAPED_TEXT=$(echo "$CLIPBOARD_TEXT" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))")

# Send POST request to the Python server
RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{\"text\": $ESCAPED_TEXT}" \
    --max-time 60)

# Check if request was successful
if [ $? -eq 0 ]; then
    # Optional: show success notification
    notify-send "Grammar Checker" "Analysis complete!" -u low
else
    notify-send "Grammar Checker" "Failed to connect to server!" -u critical
fi