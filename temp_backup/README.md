# Wikipedia Conspiracy Generator

## Overview

This project is a **Wikipedia-based Conspiracy Generator** that retrieves Wikipedia content, stores it in Elasticsearch, and uses **Gemini AI** to generate conspiracy theories linking different topics together. The system is built using Flask for API management and leverages Elasticsearch for efficient search and retrieval.

## Features

- **Elasticsearch Integration**: Stores Wikipedia summaries and allows efficient querying.
- **Gemini AI-powered Conspiracy Generation**: Generates fictional conspiracy theories by linking Wikipedia topics.
- **Flask API**: Provides an endpoint to input keywords and retrieve AI-generated conspiracy theories.
- **Docker Support**: Fully containerized for easy deployment.
- **Automated Data Processing**: Cleans and imports Wikipedia summaries into Elasticsearch.

## Project Structure

```
📂 project-root/
│── Data/                     # Directory containing data files
│   │── cleanData.py          # Script for cleaning Wikipedia data
│   │── cleaned_2024Data.json # Processed and structured data
│   └── conspiracyData.json   # Raw Wikipedia conspiracy-related data
│── Dockerfile                # Container for data import service
│── Dockerfile.api            # Container for Flask API service
│── docker-compose.yml        # Manages multi-container setup
│── import_script.py          # Handles Wikipedia data import into Elasticsearch
│── search_api.py             # Flask API to interact with the system
│── requirements.txt          # Python dependencies
│── .env                      # Environment variables (API keys, etc.)
│── README.md                 # Project documentation
```

## Setup & Installation

### Prerequisites

- **Docker & Docker Compose**
- **Python 3.9+** (if running locally)

### Steps to Run

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-root
```

#### 2. Run with Docker

```bash
docker-compose up --build
```

#### Open another terminal

```bash
(Only First Time) docker exec -it 5914projectcopy-uploader-1 python3 /app/import_script.py;
curl 'http://127.0.0.1:5002/generate?q=Keyword1,Keyword2'
```

This will:

- Start **Elasticsearch** on `http://localhost:9200`
- Run the **data importer** to populate Elasticsearch
- Launch the **Flask API**

#### 3. Run Locally (Without Docker)

```bash
pip install -r requirements.txt
python import_script.py  # Load data into Elasticsearch
python search_api.py     # Start the Flask API
```

## API Usage

### Generate Conspiracy Theory

**Endpoint:**

```
GET /generate?q=<keyword1,keyword2,...>
```

**Example Request:**

```bash
curl "http://localhost:5002/generate?q=NASA,Pizza"
```

**Example Response:**

```json
{
  "keywords": ["NASA", "Pizza"],
  "generated_conspiracy": "A wild theory connecting NASA and pizza...",
  "wikipedia_sources": [
    { "title": "NASA", "url": "https://en.wikipedia.org/wiki/NASA" },
    { "title": "Pizza", "url": "https://en.wikipedia.org/wiki/Pizza" }
  ]
}
```

## Configuration

- **Elasticsearch Host**: Configured in `docker-compose.yml` and `.env` file (`http://localhost:9200`)
- **Gemini AI Key**: Set in `.env` file
- **API Port**: Flask runs on `localhost:5002`

### API Key Security

1. Edit the `.env` file and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ES_HOST=http://localhost:9200
   ```
2. The `.env` file should be added to your `.gitignore` to prevent committing sensitive information to version control.
3. You can obtain a Gemini API key from https://ai.google.dev/

## Future Enhancements

- Improve **query expansion** for better Wikipedia search results.
- Add **multi-language support** for non-English topics.
- Implement **user feedback mechanism** to refine AI-generated conspiracies.

## Contributors

- **[Zhuoyang Li]** - Developer & Maintainer
