# Bruk Python 3.9 som base for backend
FROM python:3.9-slim AS backend

# Sett arbeidskatalog til /app for backend
WORKDIR /app

# Installer systemavhengigheter
RUN apt-get update && apt-get install -y \
    wget curl unzip nodejs npm \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgl1-mesa-glx libgtk-3-0 libnss3 libasound2 libxtst6 \
    libatk-bridge2.0-0 libatk1.0-0 libappindicator3-1 \
    libgdk-pixbuf2.0-0 libgbm1 xdg-utils fonts-liberation \
    libvulkan1 gnupg unixodbc unixodbc-dev gcc g++ \
    libpq-dev libgconf-2-4 libxss1 libodbc1 \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb \
    && apt-get -f install -y \
    && rm -rf /var/lib/apt/lists/*

# Kopier backend-filer fra PyFiles
COPY src/PyFiles /app

# Installer Python-avhengigheter
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install pyodbc gunicorn chromedriver-autoinstaller

# Installer Chrome og Chromedriver
RUN python -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()" \
    && google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://example.com

# Eksponer port 8080 for backend
EXPOSE 8080

# Sett standardport
ENV PORT=8080

# Gjør start.sh kjørbar
RUN chmod +x /app/start.sh

# Start backend
CMD ["/bin/bash", "/app/start.sh"]
