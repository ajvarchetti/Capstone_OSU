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
│── Dockerfile                # Defines the container environment
│── docker-compose.yml        # Manages multi-container setup
│── import_script.py          # Handles Wikipedia data import into Elasticsearch
│── conspiracy_generator.py   # Generates conspiracy theories using Gemini AI
│── app.py                    # Flask API to interact with the system
│── conspiracyData.json       # Raw Wikipedia conspiracy-related data
│── cleaned_conspiracyData.json  # Processed and structured data
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
This will:
- Start **Elasticsearch** on `http://localhost:9200`
- Run the **data importer** to populate Elasticsearch
- Launch the **Flask API**

#### 3. Run Locally (Without Docker)
```bash
pip install -r requirements.txt
python import_script.py  # Load data into Elasticsearch
python app.py  # Start the Flask API
```

## API Usage
### Generate Conspiracy Theory
**Endpoint:**
```
GET /generate?q=<keyword1,keyword2,...>
```
**Example Request:**
```bash
curl "http://localhost:5000/generate?q=NASA,Pizza"
```
**Example Response:**
```json
{
  "keywords": ["NASA", "Pizza"],
  "generated_conspiracy": "A wild theory connecting NASA and pizza...",
  "wikipedia_sources": [
    {"title": "NASA", "url": "https://en.wikipedia.org/wiki/NASA"},
    {"title": "Pizza", "url": "https://en.wikipedia.org/wiki/Pizza"}
  ]
}
```

## Configuration
- **Elasticsearch Host**: Configured in `docker-compose.yml` (`http://localhost:9200`)
- **Gemini AI Key**: Set in `conspiracy_generator.py`
- **API Port**: Flask runs on `localhost:5000`

## Future Enhancements
- Improve **query expansion** for better Wikipedia search results.
- Add **multi-language support** for non-English topics.
- Implement **user feedback mechanism** to refine AI-generated conspiracies.

## Contributors
- **[Your Name]** - Developer & Maintainer

## License
This project is licensed under the MIT License.
