#!/bin/bash

# Oppdater og installer nødvendige systempakker
sudo apt-get update && sudo apt-get install -y \
    wget \
    curl \
    unzip \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgl1 \
    libgtk-3-0 \
    libnss3 \
    libasound2-data \
    libxtst6 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libappindicator3-1 \
    libgdk-pixbuf2.0-0 \
    libgbm1 \
    xdg-utils \
    fonts-liberation \
    libvulkan1 \
    gnupg \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Last ned og installer Google Chrome
curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o google-chrome-stable_current_amd64.deb \
    && sudo apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Legg til Google Chrome i PATH
export PATH="/usr/bin:$PATH"
export CHROME_BIN="/usr/bin/google-chrome"

# Test Google Chrome-installasjonen
which google-chrome && google-chrome --version

# Naviger til mappen der appen og requirements.txt ligger
cd /home/site/wwwroot/src/PyFiles

# Installer Python-avhengigheter
sudo apt-get install -y python3-pip
pip3 install --no-cache-dir -r requirements.txt

# Test chromedriver_autoinstaller og Google Chrome
python3 -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()" \
    && google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://example.com

# Sett opp Gunicorn for å kjøre Flask-appen
sudo apt-get install -y gunicorn
gunicorn --bind 0.0.0.0:$PORT app:app
