from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import google.generativeai as genai

# Configure Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Configure Gemini API
GENAI_API_KEY = "AIzaSyBW-UAEJochNjflBPRp10kXl3l9CJd8B2w"
genai.configure(api_key=GENAI_API_KEY)

app = Flask(__name__)

def search_wikipedia(query):
    """
    Search Wikipedia data in Elasticsearch
    """
    es_query = {"query": {"match": {"title": query}}}
    response = es.search(index="wikipedia_conspiracies", body=es_query)

    if not response["hits"]["hits"]:
        return None

    # Get the first matching result
    result = response["hits"]["hits"][0]["_source"]
    return result

def generate_conspiracy(keywords, wiki_data):
    """
    Use Gemini to generate a conspiracy theory
    """
    model = genai.GenerativeModel("gemini-pro")

    # Construct the prompt with multiple keywords
    prompt = f"""
    You are an expert conspiracy theorist. Using the following Wikipedia summaries about {', '.join(keywords)}, 
    create a conspiracy theory that links them together into a secret plot.

    Wikipedia Data:
    """
    
    for data in wiki_data:
        prompt += f"\n- **{data['title']}**: {data['wikipedia_content']}\n"

    prompt += """
    Now, create a detailed and engaging conspiracy theory connecting these elements. Be creative and persuasive.
    """

    response = model.generate_content(prompt)
    return response.text

@app.route("/generate", methods=["GET"])
def generate():
    """
    Users provide multiple keywords, search Wikipedia data, and let Gemini generate a conspiracy theory
    """
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    keywords = query.split(",")  # Allow multiple keywords input, e.g., "NASA,Pizza"
    wiki_data = []

    for keyword in keywords:
        keyword = keyword.strip()
        wiki_entry = search_wikipedia(keyword)
        if wiki_entry:
            wiki_data.append(wiki_entry)

    if not wiki_data:
        return jsonify({"error": "No Wikipedia data found for the provided keywords"}), 404

    # Generate conspiracy theory
    conspiracy_text = generate_conspiracy(keywords, wiki_data)

    return jsonify({
        "keywords": keywords,
        "generated_conspiracy": conspiracy_text,
        "wikipedia_sources": [{"title": d["title"], "url": d["source_url"]} for d in wiki_data]
    })

if __name__ == "__main__":
    app.run(debug=True)
