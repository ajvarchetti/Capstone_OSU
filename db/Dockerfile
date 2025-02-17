FROM python:3.9-slim

WORKDIR /app
COPY output.json /app/output.json
COPY import_script.py /app/import_script.py

RUN pip install elasticsearch requests

CMD ["python", "import_script.py"]