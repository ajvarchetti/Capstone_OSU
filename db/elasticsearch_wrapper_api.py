from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
import google.generativeai as genai
import os
import time

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

def generate_conspiracy(keywords, wiki_data):
    """
    Use Gemini AI to generate a conspiracy theory
    """
    if not GEMINI_API_KEY:
        return "Error: Gemini API key is not set."

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        return f"❌ Error initializing Gemini model: {e}"

    prompt = f"""
    You are a writer of absurd fictional conspiracy theories. They should be plausible (but do not need to be truthful), creative, entertaining and most of all, funny.
    The conspiracy theory should be relatively simple and easy to understand, and between 5-8 sentences long.
    You are given two topics and their respective wikipedia articles. Try to use information from the wikipedia articles to link the topics together in a humerous way.
    The topics are: {', '.join(keywords)}.

    Wikipedia data for each term will be delimited as - **term**: <content>

    If a piece of information is not relevant to the conspiracy theory, do not include it in the response.
    If a given topic is fictional, you may include the factual information about it's creation and factual history, but do not include any information about the fictional world it is set in.
    If the topics supplied are NSFW, vulgar, or otherwise inappropriate, please do not generate a conspiracy theory. Instead, return a message saying "Sorry, I can't help with that."
    Do not admit that the conspiracy theory is fictional, and do not include any disclaimers or other text in the response.
    """
    
    for data in wiki_data:
        prompt += f"\n- **{data['title']}**: <{data.get('wikipedia_content', 'Content not available')}>\n"

    try:
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "Error: Invalid response format."
    except Exception as e:
        return f"❌ Gemini API error: {e}"

@app.route("/generate", methods=["GET"])
def generate():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query"}), 400

    keywords = [k.strip() for k in query.split(",")]
    wiki_data = [search_wikipedia(k) for k in keywords if search_wikipedia(k)]

    if not wiki_data:
        return jsonify({"error": "No Wikipedia data found for the provided keywords"}), 404

    conspiracy_text = generate_conspiracy(keywords, wiki_data)

    return jsonify({
        "keywords": keywords,
        "generated_conspiracy": conspiracy_text,
        "wikipedia_sources": [
            {"title": d["title"], "url": d.get("source_url", "N/A")} 
            for d in wiki_data
        ]
    })

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