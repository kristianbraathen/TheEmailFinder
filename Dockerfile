# --- Bygg frontend ---
FROM node:18-alpine AS frontend

WORKDIR /frontend

# Kopier package.json og package-lock.json
COPY package.json package-lock.json ./

# Installer npm-avhengigheter
RUN npm install

# Kopier frontend-koden fra src/
COPY src /frontend/src

# Bygg Vue-prosjektet
RUN npm run build


# --- Bygg backend ---
FROM python:3.9-slim AS backend

WORKDIR /app

# Installer systemavhengigheter (inkludert Chrome + ChromeDriver dependencies)
RUN apt-get update && apt-get install -y \
    wget curl unzip nodejs npm dos2unix \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgl1-mesa-glx libgtk-3-0 libnss3 libasound2 libxtst6 \
    libatk-bridge2.0-0 libatk1.0-0 libappindicator3-1 \
    libgdk-pixbuf2.0-0 libgbm1 xdg-utils fonts-liberation \
    libvulkan1 gnupg unixodbc unixodbc-dev gcc g++ \
    libpq-dev libgconf-2-4 libxss1 libodbc1 bash && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install && \
    rm google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Kopier hele prosjektet til /app
COPY . /app

# Kopier WebJob-koden inn i containeren (fra lokalt prosjekt)
COPY App_Data/jobs/triggered/webjobemailsearch /app/App_Data/jobs/triggered/webjobemailsearch

# Sett riktige rettigheter
RUN chmod -R 755 /app

# Installer Python-avhengigheter
RUN pip install --no-cache-dir -r /app/src/PyFiles/requirements.txt \
    && pip install pyodbc gunicorn chromedriver-autoinstaller

# Kopier frontend-bygg fra frontend stage
COPY --from=frontend /frontend/dist /app/dist

RUN ls -la /app/dist

# Kopier start.sh og gjør den kjørbar
COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# Miljøvariabler
ENV CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

ENV PORT=80
ENV PYTHONPATH=/app/src/PyFiles

EXPOSE 80

# Start appen
CMD ["/app/start.sh"]
