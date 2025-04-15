from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
import google.generativeai as genai
import os
import time
from datetime import datetime
from es_gen_models import genV1, genV2, genV3

# Configure Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
print(f"🔌 Will attempt connecting to Elasticsearch at {ES_HOST}")

MAX_RETRIES = 10
RETRY_DELAY = 5  # seconds

es = None
connected = False
for attempt in range(MAX_RETRIES):
    try:
        es_temp = Elasticsearch([ES_HOST], verify_certs=False)
        if es_temp.ping():
            es = es_temp
            connected = True
            print(f"✅ Connected to Elasticsearch on attempt {attempt+1}")
            break
        else:
            print(f"Attempt {attempt+1}: Elasticsearch not reachable, retrying in {RETRY_DELAY}s...")
    except Exception as e:
        print(f"⚠️ Elasticsearch error on attempt {attempt+1}: {e}")
    time.sleep(RETRY_DELAY)

if not connected:
    print("❌ Gave up connecting to Elasticsearch after multiple retries.")
else:
    print("✅ Elasticsearch connection established.")

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ Gemini API key not set. Check .env file.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini API configured successfully")
    except Exception as e:
        print(f"❌ Gemini API initialization failed: {e}")

app = Flask(__name__)
CORS(app)

def search_wikipedia(query):
    """
    Search Wikipedia data in Elasticsearch
    """
    print(f"🔍 Searching for: {query}")
    es_query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": query}},
                    {"match": {"wikipedia_content": query}}
                ]
            }
        }
    }
    
    try:
        if not es or not connected:
            print("❌ Elasticsearch is not connected.")
            return None

        if not es.indices.exists(index="wikipedia"):
            print(f"❌ Index 'wikipedia' does not exist")
            return None
            
        response = es.search(index="wikipedia", query=es_query["query"])
        hits = response.get("hits", {}).get("hits", [])
        
        if not hits:
            print(f"⚠️ No Wikipedia data found for query: {query}")
            return None
        
        print(f"✅ Found {len(hits)} results for {query}")
        return hits[0]["_source"]
    except Exception as e:
        print(f"❌ Elasticsearch error: {e}")
        return None

# API Endpoints
@app.route("/generate", methods=["GET"])
def generate():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    obj = genV2(es, connected, GEMINI_API_KEY, query)
    # obj = genV1(es, connected, GEMINI_API_KEY, query)

    return obj

@app.route("/samples", methods=["GET"])
def getSamples():
    numTopics = 50  # Default number of topics to fetch

    if not es or not connected:
        print("❌ Elasticsearch is not connected.")
        return None

    if not es.indices.exists(index="wikipedia"):
        print(f"❌ Index 'wikipedia' does not exist")
        return None

    try:
        seed = int(datetime.now().strftime("%H%M%S"))  # Use current time as seed
    except ValueError as e:
        print(f"⚠️ Error generating seed from datetime: {e}")
        seed = 0  # Fallback to a default seed value

    try:
        response = es.search(
            index="wikipedia",
            body={
                "size": numTopics,
                "_source": ["title"],
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "random_score": {"seed": seed, "field": "_seq_no"}
                    }
                }
            }
        )
        
        samples = [hit["_source"]["title"] for hit in response["hits"]["hits"]]
    except Exception as e:
        return jsonify({"error": f"Failed to fetch samples: {str(e)}"}), 500

    return jsonify(samples)

@app.route("/debug/status", methods=["GET"])
def debug_status():
    status = {
        "elasticsearch": {
            "host": ES_HOST, 
            "connected": False, 
            "error": None, 
            "index_exists": False
        },
        "gemini_api": {
            "configured": bool(GEMINI_API_KEY), 
            "error": None, 
            "model_initialized": False
        },
        "app_info": {
            "flask_debug": app.debug, 
            "port": 5002
        }
    }

    try:
        # Convert to bool explicitly so we don't store the response object.
        ping_response = es.ping()
        status["elasticsearch"]["connected"] = bool(ping_response)

        index_exists_response = es.indices.exists(index="wikipedia")
        status["elasticsearch"]["index_exists"] = bool(index_exists_response)

        # Only fetch document count if the index truly exists
        if status["elasticsearch"]["index_exists"]:
            count_resp = es.count(index="wikipedia")
            status["elasticsearch"]["document_count"] = count_resp.get("count", 0)

    except Exception as e:
        status["elasticsearch"]["error"] = str(e)

    # Check Gemini configuration
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            status["gemini_api"]["model_initialized"] = True
        except Exception as e:
            status["gemini_api"]["error"] = str(e)

    return jsonify(status)

if __name__ == "__main__":
    # Disable output buffering for immediate logs.
    # You can also set ENV PYTHONUNBUFFERED=1 in your Dockerfile
    os.environ["PYTHONUNBUFFERED"] = "1"
    app.run(host="0.0.0.0", port=5002, debug=True, threaded=True)