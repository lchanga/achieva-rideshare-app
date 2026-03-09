# We're switching to 'bullseye' (Debian 11) specifically to match the MS drivers
FROM python:3.11-bullseye

# Set working directory
WORKDIR /app

# Install the Microsoft Drivers using the official one-liner for Debian 11
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

# Copy requirements and install
COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy the rest of the app
COPY . .

# Flask stuff
EXPOSE 5000
CMD ["python", "-m", "server.run"]