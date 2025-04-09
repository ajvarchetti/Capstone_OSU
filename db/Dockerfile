FROM python:3.9-slim AS base

WORKDIR /db

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as with-chrome

# Install chrome and chromedriver for Selenium
RUN apt-get update -qq -y
RUN apt-get install zip unzip
RUN apt-get install -y \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-4-1 \
        libnss3 \
        xdg-utils \
        wget
RUN wget -q -O chrome-linux64.zip https://bit.ly/chrome-linux64-121-0-6167-85
RUN unzip chrome-linux64.zip
RUN rm chrome-linux64.zip
RUN mv chrome-linux64 /opt/chrome/
RUN ln -s /opt/chrome/chrome /usr/local/bin/
RUN wget -q -O chromedriver-linux64.zip https://bit.ly/chromedriver-linux64-121-0-6167-85
RUN unzip -j chromedriver-linux64.zip chromedriver-linux64/chromedriver
RUN rm chromedriver-linux64.zip
RUN mv chromedriver /usr/local/bin/

# Test stage
FROM with-chrome as test

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Command to run tests
CMD ["python", "-m", "pytest"]