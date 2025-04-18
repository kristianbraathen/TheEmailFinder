# --- Bygg frontend ---
FROM node:18-alpine AS frontend

WORKDIR /frontend

# Kopier package.json og package-lock.json fra toppenivået
COPY package.json package-lock.json ./

# Installer npm-avhengigheter
RUN npm install

# Kopier resten av frontend-koden fra src/
COPY src /frontend/src

# Bygg Vue-prosjektet
RUN npm run build

# --- Bygg backend ---
FROM python:3.9-slim AS backend

WORKDIR /app

# Installer systemavhengigheter
RUN apt-get update && apt-get install -y \
    wget curl unzip nodejs npm dos2unix \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgl1-mesa-glx libgtk-3-0 libnss3 libasound2 libxtst6 \
    libatk-bridge2.0-0 libatk1.0-0 libappindicator3-1 \
    libgdk-pixbuf2.0-0 libgbm1 xdg-utils fonts-liberation \
    libvulkan1 gnupg unixodbc unixodbc-dev gcc g++ \
    libpq-dev libgconf-2-4 libxss1 libodbc1 bash && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || true && \
    apt-get install -f -y && \
    rm google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/*


# Kopier hele prosjektet, inkludert package.json
COPY . /app

# Sett riktige rettigheter på filene
RUN chmod -R 755 /app

# Installer backend-avhengigheter
RUN pip install --no-cache-dir -r /app/src/PyFiles/requirements.txt \
    && pip install pyodbc gunicorn chromedriver-autoinstaller

# Kopier frontend-bygg fra tidligere steg til Flask static-mappe
COPY --from=frontend /frontend/dist /app/dist

# Kopier start.sh og gjør den kjørbar
COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# Sett miljøvariabler
ENV CHROME_BIN="/usr/bin/google-chrome"
ENV PORT=8080
ENV PYTHONPATH=/app/src/PyFiles

EXPOSE 80

# Start appen
CMD ["/app/start.sh"]