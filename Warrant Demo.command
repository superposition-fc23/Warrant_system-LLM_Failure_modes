#!/bin/zsh
# Double-click to start the local demo server and open the prototype.
cd "$(dirname "$0")/ai-stack"
(sleep 1; open "http://127.0.0.1:8765/") &
exec .venv/bin/python demo_server.py
