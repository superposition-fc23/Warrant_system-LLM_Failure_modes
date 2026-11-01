#!/bin/zsh
# Resets index.html, prototype.html and slides.html to the blank templates. Destroys work in progress: commit or copy first.
cd "$(dirname "$0")" && cp .blank-index.html index.html && cp .blank-prototype.html prototype.html && cp .blank-slides.html slides.html && echo "index.html, prototype.html and slides.html reset to blank templates"
