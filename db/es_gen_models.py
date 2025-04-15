from elasticsearch import Elasticsearch
from elasticsearch import helpers
from flask import jsonify
import google.generativeai as genai
import requests
from requests.utils import quote


# Cleans duplicate hits from Elasticsearch results based on the title field
def clean_duplicate_hits(hits):
    unique_hit_titles = []
    unique_hits = []

    for hit in hits:
        title = hit['title']
        if title not in unique_hit_titles:
            unique_hit_titles.append(title)
            unique_hits.append(hit)

    print(f"Cleaned {len(hits) - len(unique_hits)} duplicate hits")
    return unique_hits

# Fetch from Wikipedia API Method
def fetch_from_wiki_api(es: Elasticsearch, connected: bool, topic: str) -> list:
    if not es or not connected:
        print("❌ Failed Wiki Fetch, Elasticsearch is not connected.")
        return None

    print(f"🔍 Fetching from Wikipedia API for topic: {topic}")
    
    try:
        WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        # Use URL encoding for the topic
        url = WIKI_API_URL + quote(topic)
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            wiki_data = response.json()
            content = wiki_data.get("extract", "No content available.")
            t = wiki_data.get("type", "ambiguous")

            if t != "standard" or content == "No content available." or content == "":
                print(f"⚠️ Wikipedia returned 'No content available' for: {topic}")
                return None
            page_url = wiki_data.get("content_urls", {}).get("desktop", {}).get("page", "")
            doc = {
                "title": topic.lower(),
                "label": topic,
                "views": -1,
                "wikipedia_content": content,
                "source_url": page_url
            }
            action = {
                "_op_type": "update",
                "_index": "wikipedia_conspiracies",
                "_id": doc["title"],
                "doc": doc,
                "doc_as_upsert": True
            }
            helpers.bulk(es, [action])
            print(f"✅ Wiki API Found Data for: {topic}")
            print(doc['wikipedia_content'])
            return doc
        else:
            print(f"⚠️ Wikipedia API returned status code {response.status_code} for topic: {topic}")
            return None
    except Exception as e:
        print(f"❌ Error fetching from Wikipedia API: {e}")
        return None

# Function to call Elasticsearch and return results for a given query
def call_es(es: Elasticsearch, connected: bool, topic: str, es_query: dict):
    try:
        if not es or not connected:
            print("❌ Elasticsearch is not connected.")
            return None

        if not es.indices.exists(index="wikipedia"):
            print(f"❌ Index 'wikipedia' does not exist")
            return None
            
        response = es.search(index="wikipedia", query=es_query["query"], size=es_query.get("size", 10))
        hits = response.get("hits", {}).get("hits", [])

        # Call Wikipedia API if no hits are found
        if not hits:
            print(f"⚠️ No Wikipedia data found for elastic search query: {topic}")
            # hit = fetch_from_wiki_api(es, connected, topic)

            # if hit is None:
            #     return None
            # return [hit]
            return None

        print(f"✅ Found {len(hits)} results for {topic}")
        for hit in hits:
            print(f" - {hit['_source']['title']}")

        return [hit["_source"] for hit in hits]
    except Exception as e:
        print(f"❌ Elasticsearch error: {e}")
        return None


## Elasticsearch Models

# Helper function: Create a span clause for fuzzy matching
def create_span_clause(word: str, field: str, fuzz: int) -> dict:
    return {
        "span_multi": {
            "match": {
                "fuzzy": {
                    field: {
                        "value": word,
                        "fuzziness": fuzz
                    }
                }
            }
        }
    }

# Creates the clause necessary for multi-word fuzzy search in ES.
def create_span_near_query(topic: str, field: str, fuzz: int = 2) -> dict:
    topic_list = topic.split(" ")
    span_dict = {
        "span_near": {
            "clauses": [],
            "slop": 0,
            "in_order": True
        }
    }
    for word in topic_list:
        span_clause = create_span_clause(word, field, fuzz)
        span_dict["span_near"]["clauses"].append(span_clause)
    return span_dict

# Searches for a topic in Elasticsearch. If no results are found, tries to fetch from the Wikipedia API.
def esField(es: Elasticsearch, connected: bool, topic: str, field: str, fuzz=1) -> str:
    print(f"🔍 Searching for: {topic}")
    es_query = {
        "query": {
            "bool": {
                "should": [
                    create_span_near_query(topic, field, fuzz),
                ]
            }
        },
        "size": 50
    }
    hits = call_es(es, connected, topic, es_query)

    # If no hits are found, try to fetch data from the Wikipedia API
    if hits is not None:
        hits = clean_duplicate_hits(hits)
        return hits

    return None

# Takes a connection to ES with every function call.
# Searches for one topic in Elasticsearch.
def esV1(es: Elasticsearch, connected: bool, topic: str, fuzz: int = 2) -> str:
    print(f"🔍 Searching for: {topic}")
    es_query = {
        "query": {
            "bool": {
                "should": [
                    create_span_near_query(topic, "title", fuzz),
                    create_span_near_query(topic, "wikipedia_content", fuzz)
                ]
            }
        },
        "size": 50
    }
    hits = call_es(es, connected, topic, es_query)
    if hits is not None:
        hits = clean_duplicate_hits(hits)
        return hits
    return None

# Uses a relaxed matching logic to search for Wikipedia data in ES,
# aiming to return documents that contain either topic1, topic2, or both.
def esV2(es: Elasticsearch, connected: bool, topic1: str, topic2: str, fuzz: int = 1) -> str:
    """
    Search Wikipedia data in Elasticsearch
    """
    print(f"🔍 Searching for topic between: {topic1} and {topic2}")
    es_query = {
        "query": {
            "bool": {
                "must": [{
                    "bool": {
                        "should": [
                            create_span_near_query(topic1, "title", fuzz),
                            create_span_near_query(topic1, "wikipedia_content", fuzz)
                        ]
                    },
                    "bool": {
                        "should": [
                            create_span_near_query(topic2, "title", fuzz),
                            create_span_near_query(topic2, "wikipedia_content", fuzz)
                        ]
                    }
                }]
            }
        },
        "size": 50
    }
    
    # is none if ES is not connected or index does not exist
    hits = call_es(es, connected, topic1 + " and " + topic2, es_query)

    if hits is not None:
        hits = clean_duplicate_hits(hits)
        hits = hits[:10] if len(hits) > 10 else hits

        return hits
    return None

## Gemini Prompts
def consp_promptV1(keywords, wiki_data) -> str:
    prompt = f"""
    You are an expert in historical mysteries. Using only the information contained in the following Wikipedia 
    summaries about {', '.join(keywords)}, create a fascinating story that connects them. You may leave out information that is not relevant to the story, but do not 
    hallucinate false information.

    Wikipedia Data:
    """
    for data in wiki_data:
        prompt += f"\n- **{data['title']}**: {data.get('wikipedia_content', 'Content not available')}\n"
    prompt += "Now, craft an engaging and imaginative story that weaves these elements together."
    return prompt

# Utilize Tree of Thoughts Prompting 
def consp_promptV2(keywords, wiki_data) -> str:
    prompt = f"""
    Imagine there are five experts on creating concise conspiracy theories. They all sit in a room, 
    collaborating on a response to this prompt. They each write a draft of their thinking based on 
    the provided Wikipedia summaries. Then they all share with the group of other experts. With each 
    iteration, they will refine their responses based on the feedback of the other experts and how well 
    it follows the rules of the prompt. The rules are absolute and must be followed. This process of 
    draft and revision is iterated several times. At the end, before, they will review all their 
    responses to the prompt and select the most compelling one. The response they select will then be 
    condensed into a single concise conspiracy theory that is no more than 8 sentences long. This 
    agreed upon conspiracy is the only thing that will be returned to the user.

    Both of these keywords will be used below in the rules
    KEYWORD1: {keywords[0]}
    KEYWORD2: {keywords[-1]}

    The rules for each expert conspiracy author are as follows:
    1. You may ONLY use information contained in the provided Wikipedia summaries.
    2. Your conspiracy must not agree with commonly accepted historical narratives.
    3. The conspiracy must begin with either the topic KEYWORD1 or the topic KEYWORD2.
    4. The conspiracy must use KEYWORD1 and KEYWORD2 as key elements in the story.
    5. Facts and timelines must be consistent with the provided Wikipedia summaries but may be miss-interpreted.
    6. The conspiracy must be non-falsifiable and open to interpretation.
    7. The conspiracy must cite statistics found in a wikipedia summary at least once
    8. The conspiracy must have a timeline of events
    9. Sentences should not be run-on.

    Wikipedia Summaries:
    """

    for data in wiki_data:
        prompt += f"\n- **{data['title']}**: {data.get('wikipedia_content', 'Content not available')}\n"

    return prompt


def gem_consp(GEMINI_API_KEY, keywords, wiki_data):
    """
    Use Gemini AI to generate a conspiracy theory.
    """
    if not GEMINI_API_KEY:
        return "Error: Gemini API key is not set."

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        return f"❌ Error initializing Gemini model: {e}"


    prompt = consp_promptV2(keywords, wiki_data)


    try:
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "Error: Invalid response format."
    except Exception as e:
        return f"❌ Gemini API error: {e}"

# Helper functions for ES and Gemini API
def report_es_results(keywords, wiki_data):
    print(f"Retrieved Wikipedia data for keywords: {keywords}")
    print(f"Wikipedia data: {[w['title'] for w in wiki_data]}")

def gen_json_output(keywords, conspiracy_text, wiki_data):
    return jsonify({
        "keywords": keywords,
        "generated_conspiracy": conspiracy_text,
        "wikipedia_sources": [
            {"title": d["title"], "url": d.get("source_url", "N/A")}
            for d in wiki_data
        ]
    })

## Base Generation Models for ES and Gemini API

def genV1(es, connected, GEMINI_API_KEY, query):
    keywords = [k.strip() for k in query.split(",")]
    wiki_data = []
    for k in keywords:
        hit = esV1(es, connected, k)
        if hit is not None:
            wiki_data.extend(hit)

    if not wiki_data:
        return jsonify({"error": "No Wikipedia data found for the provided keywords"}), 404

    report_es_results(keywords, wiki_data)
    conspiracy_text = gem_consp(GEMINI_API_KEY, keywords, wiki_data)
    return gen_json_output(keywords, conspiracy_text, wiki_data)

def genV2(es, connected, GEMINI_API_KEY, query):
    keywords = [k.strip() for k in query.split(",")]

    if len(keywords) < 2:
        return jsonify({"error": "Please provide at least two keywords for comparison"}), 400

    wiki_data = []

    # Check for cross-reference hits first using the relaxed query logic
    print(" ----- Step (1 / 2) -----")
    print(f"🔁 Cross Reference: {keywords[0]} and {keywords[1]}")
    cross_ref_hits = esV2(es, connected, keywords[0], keywords[1])
    if cross_ref_hits:
        print(f"✅ Cross-ref hits found: {[h['title'] for h in cross_ref_hits]}")
        wiki_data.extend(cross_ref_hits)
    else:
        print(f"⚠️ No cross-ref hits found for: {keywords[0]} and {keywords[1]}")

    # Add individual hits for each keyword, triggering Wikipedia fallback if not in ES
    print(" ----- Step (2 / 2) -----")
    print("🔁 Individual Keyword Search")
    for keyword in keywords:
        print(f"🔍 Querying: {keyword}")
        hit = esField(es, connected, keyword, "title")
        if hit:
            print(f"✅ Data found for {keyword}: {[h['title'] for h in hit]}")
            wiki_data.extend(hit)
        else:
            print(f"❌ No data found for keyword: {keyword}")

    print("----- Finished ------")

    if not wiki_data:
        return jsonify({"error": "No Wikipedia data found for the provided keywords"}), 404

    # Remove duplicates based on title
    wiki_data = clean_duplicate_hits(wiki_data)
    report_es_results(keywords, wiki_data)
    conspiracy_text = gem_consp(GEMINI_API_KEY, keywords, wiki_data)

    return gen_json_output(keywords, conspiracy_text, wiki_data)

def genV3(es, connected, GEMINI_API_KEY, query, depth=2):
    keywords = [k.strip() for k in query.split(",")]

    if len(keywords) < 2:
        return jsonify({"error": "Please provide at least two keywords for comparison"}), 400

    wiki_data = []
    # Get information for each keyword individually
    for keyword in keywords:
        hit = esField(es, connected, keyword, "title")
        if hit:
            wiki_data.append(hit[0])  # Assume the first hit is the desired topic
        else:
            return jsonify({"error": f"⚠️ No hits found for keyword: {keyword} - Exiting Search"}), 400

    # Recursive cross-reference function
    def cross_ref(topic1, topic2, depth, black_list=[]):
        black_list = black_list.copy()
        black_list.extend([topic1.lower(), topic2.lower()])

        if depth <= 0:
            return ([], 0)

        hits = esV2(es, connected, topic1, topic2)
        if not hits:
            return ([], 0)

        sub_hits = []  # tuples: ([start->middle topics], middle topic, [middle->end topics], total topics, total views)
        for hit in hits:
            hit_title = hit['title']
            if hit_title.lower() in black_list:
                continue

            (sm, sm_views) = cross_ref(topic1, hit_title, depth - 1, black_list)
            sm_titles = [t['title'].lower() for t in sm]

            (me, me_views) = cross_ref(hit_title, topic2, depth - 1, black_list + sm_titles)
            hit_views = hit.get('views', 0) if isinstance(hit.get('views'), int) else 0
            sub_views = sm_views + me_views + hit_views
            sub_len = len(sm) + len(me) + 1
            sub_hits.append((sm, hit, me, sub_len, sub_views))

        if sub_hits:
            sub_hits.sort(key=lambda x: (x[3], x[4]), reverse=True)
            start = sub_hits[0][0]
            middle = sub_hits[0][1]
            end = sub_hits[0][2]
            combined_topics = start + [middle] + end
            total_views = sub_hits[0][4]
            return (combined_topics, total_views)

        return ([], 0)

    (cross_ref_hits, cross_ref_views) = cross_ref(keywords[0], keywords[1], depth)
    if not cross_ref_hits or len(cross_ref_hits) <= 0:
        return jsonify({"error": "⚠️ No cross-reference hits found - Exiting Search"}), 400

    cross_ref_hits = [wiki_data[0]] + cross_ref_hits + [wiki_data[1]]
    print(f"🔍 Cross-reference hits found: {[ch['title'] for ch in cross_ref_hits]}")
    report_es_results(keywords, cross_ref_hits)
    conspiracy_text = gem_consp(GEMINI_API_KEY, keywords, cross_ref_hits)
    return gen_json_output(keywords, conspiracy_text, cross_ref_hits)