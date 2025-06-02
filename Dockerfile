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

# Copy the entire project
COPY . /app

# Set up directories and permissions
RUN mkdir -p /home/LogFiles && \
    chmod 777 /home/LogFiles && \
    mkdir -p /app/App_Data/jobs/triggered && \
    chmod 777 /app/App_Data/jobs/triggered && \
    find /app -type f -name "*.sh" -exec chmod +x {} \; && \
    find /app -type f -name "*.sh" -exec dos2unix {} \;

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/src/PyFiles/requirements.txt \
    && pip install pyodbc gunicorn chromedriver-autoinstaller

# Copy frontend build
COPY --from=frontend /frontend/dist /app/dist

# Environment variables
ENV CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"
ENV PORT=80
ENV PYTHONPATH=/app/src/PyFiles:/app/App_Data/jobs/triggered/webjobemailsearch/src/PyFiles
ENV WEBSITE_HOSTNAME=localhost
ENV WEBSITE_SITE_NAME=webjobemailsearch
ENV WEBSITE_INSTANCE_ID=local

EXPOSE 80

# Start the app
CMD ["/app/start.sh"]
