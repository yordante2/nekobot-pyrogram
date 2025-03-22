apt-get update && apt-get install -y chromium-browser
mkdir server
python3 -m http.server -d server &
python3 neko.py
#!/bin/bash
