# Use a base image with Python and a minimal Debian environment
FROM python:3.9-slim

# Set the working directory for your application
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgl1-mesa-glx \
    libgtk-3-0 \
    libnss3 \
    libasound2 \
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
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    libpq-dev \
    libgconf-2-4 \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft's package repository for msodbcsql17
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Add Google Chrome to PATH
ENV PATH="/usr/bin:$PATH"
ENV CHROME_BIN="/usr/bin/google-chrome"

# Test Google Chrome installation
RUN which google-chrome && google-chrome --version

# Copy the application files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install pyodbc via pip after system dependencies are in place
RUN pip install pyodbc

# Install chromedriver (as per the script) and run a test
RUN python -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()" \
    && google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://example.com

# Expose port 8080 for the app
EXPOSE 8080
# Set default port value (Ensure it works in your container)
ENV PORT 8080

# Run Gunicorn to serve the Flask app
CMD gunicorn --bind 0.0.0.0:$PORT app:app
