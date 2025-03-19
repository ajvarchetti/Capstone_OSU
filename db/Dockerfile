FROM python:3.9-slim

WORKDIR /app

# Copy the API script and dependencies
COPY search_api.py /app/search_api.py
COPY import_script.py /app/import_script.py
COPY requirements.txt /app/requirements.txt
COPY Data /app/Data

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask API port
EXPOSE 5002

# Ensure the container keeps running with Flask
CMD ["python", "-u", "search_api.py"]