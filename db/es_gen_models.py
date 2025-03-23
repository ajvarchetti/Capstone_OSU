from elasticsearch import Elasticsearch
from flask import jsonify
import google.generativeai as genai

# Cleans duplicate hits from Elastic Search results based on the title field
def clean_duplicate_hits(hits):
    print(hits.type, hits[0].type)
    unique_hit_titles = {}
    unique_hits = []
    for hit in hits:
        title = hit["_source"]["title"]
        if title not in unique_hit_titles:
            unique_hit_titles[title] = hit
            unique_hits.append(hit)

    print(f"Cleaned {len(hits) - len(unique_hits)} duplicate hits")
    print(unique_hits.type, unique_hits[0].type)
    return unique_hits

# Function to call Elasticsearch and return results from a given Query
def call_es(es: Elasticsearch, connected: bool, topic: str, es_query: dict) -> str:
    try:
        if not es or not connected:
            print("❌ Elasticsearch is not connected.")
            return None

        if not es.indices.exists(index="wikipedia_conspiracies"):
            print(f"❌ Index 'wikipedia_conspiracies' does not exist")
            return None
            
        response = es.search(index="wikipedia_conspiracies", query=es_query["query"])
        hits = response.get("hits", {}).get("hits", [])
        
        if not hits:
            print(f"⚠️ No Wikipedia data found for query: {topic}")
            return None
        
        print(f"✅ Found {len(hits)} results for {topic}")
        for hit in hits:
            print(f" - {hit['_source']['title']}")

         # Return the first result (or you can modify this to return more)
        return hits[0]["_source"]
    except Exception as e:
        print(f"❌ Elasticsearch error: {e}")
        return None

## Elastic Search Models

# Take Connection to ES with every function call
# Takes two topics and returns a list of hits from ES
def esV1(es: Elasticsearch, connected: bool, topic: str) -> str:
    """
    Search Wikipedia data in Elasticsearch
    """
    print(f"🔍 Searching for: {topic}")
    es_query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": topic}},
                    {"match": {"wikipedia_content": topic}}
                ]
            }
        }
    }
    
    # is none if ES is not connected or index does not exist
    hits = call_es(es, connected, topic, es_query)

    return hits

## Gemini Prompts
def consp_promptV1(keywords, wiki_data) -> str:
    prompt = f"""
    You are an expert in historical mysteries. Using the following Wikipedia summaries about {', '.join(keywords)},
    create a fascinating story that connects them. Use a maximum of 8 sentences total for the story.

    Wikipedia Data:
    """
    
    for data in wiki_data:
        prompt += f"\n- **{data['title']}**: {data.get('wikipedia_content', 'Content not available')}\n"
    
    prompt += "Now, craft an engaging and imaginative story that weaves these elements together."

    return prompt

def gem_consp(GEMINI_API_KEY, keywords, wiki_data):
    """
    Use Gemini AI to generate a conspiracy theory
    """
    if not GEMINI_API_KEY:
        return "Error: Gemini API key is not set."

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        return f"❌ Error initializing Gemini model: {e}"

    prompt = consp_promptV1(keywords, wiki_data)

    try:
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "Error: Invalid response format."
    except Exception as e:
        return f"❌ Gemini API error: {e}"

## Base Generation Models for ES and Gemini API

def genV1(es, connected, GEMINI_API_KEY, query):
    if not query:
        return jsonify({"error": "Missing query"}), 400

    keywords = [k.strip() for k in query.split(",")]
    wiki_data = [esV1(es, connected, k) for k in keywords if esV1(es, connected, k)]

    if not wiki_data:
        return jsonify({"error": "No Wikipedia data found for the provided keywords"}), 404

    print(f"Retrieved Wikipedia data for keywords: {keywords}")
    print(f"Wikipedia data: {wiki_data[0]['title']}")
    conspiracy_text = gem_consp(GEMINI_API_KEY, keywords, wiki_data)

    return jsonify({
        "keywords": keywords,
        "generated_conspiracy": conspiracy_text,
        "wikipedia_sources": [
            {"title": d["title"], "url": d.get("source_url", "N/A")} 
            for d in wiki_data
        ]
    })
    