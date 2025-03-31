from elasticsearch import Elasticsearch
from flask import jsonify
import google.generativeai as genai

# Cleans duplicate hits from Elastic Search results based on the title field
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

# Function to call Elasticsearch and return results from a given Query
def call_es(es: Elasticsearch, connected: bool, topic: str, es_query: dict):
    try:
        if not es or not connected:
            print("❌ Elasticsearch is not connected.")
            return None

        if not es.indices.exists(index="wikipedia_conspiracies"):
            print(f"❌ Index 'wikipedia_conspiracies' does not exist")
            return None
            
        response = es.search(index="wikipedia_conspiracies", query=es_query["query"], size=es_query.get("size", 10))
        # print(response)
        hits = response.get("hits", {}).get("hits", [])
        
        if not hits:
            print(f"⚠️ No Wikipedia data found for query: {topic}")
            return None
        
        print(f"✅ Found {len(hits)} results for {topic}")
        for hit in hits:
            print(f" - {hit['_source']['title']}")

        return [hit["_source"] for hit in hits]
    except Exception as e:
        print(f"❌ Elasticsearch error: {e}")
        return None

## Elastic Search Models

# Helper function for below
def create_span_clause(word: str, field: str, fuzz: int) -> dict:
    return { 
        "span_multi": {  
            "match":{  
                "fuzzy":{  
                    field:{  
                        "value": word,
                        "fuzziness": fuzz
                    }
                }
            }
        }
    }

# Creates the clause necessary for multi-word fuzzy search in ES
# Fuzz is the number of characters that can be different in the word for a match
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

def esField(es: Elasticsearch, connected: bool, topic: str, field: str, fuzz = 1) -> str:
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
    
    # is none if ES is not connected or index does not exist
    if hits is not None:
        hits = clean_duplicate_hits(hits)
        return hits
    return None

# Take Connection to ES with every function call
# Takes two topics and returns a list of hits from ES
def esV1(es: Elasticsearch, connected: bool, topic: str, fuzz: int = 2) -> str:
    """
    Search Wikipedia data in Elasticsearch
    """
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
    
    # is none if ES is not connected or index does not exist
    if hits is not None:
        hits = clean_duplicate_hits(hits)
        # hits = hits[:10] if len(hits) > 10 else hits

        return hits
    return None

# Finds a topic that is related to another topic
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

# Helper Functions For ES and Gemini API
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

# Takes the two topics and uses a cross-reference search to find a connection
# Keywords for gemini include the two topics and results from overlapping
# topics (title or wikipedia_content)
def genV2(es, connected, GEMINI_API_KEY, query):
    keywords = [k.strip() for k in query.split(",")]

    if len(keywords) < 2:
        return jsonify({"error": "Please provide at least two keywords for comparison"}), 400
    
    wiki_data = []

    # Check for cross-reference hits first
    cross_ref_hits = esV2(es, connected, keywords[0], keywords[1])
    if cross_ref_hits:
        wiki_data.extend(cross_ref_hits)

    # Add individual hits for each keyword
    for keyword in keywords:
        hit = esV1(es, connected, keyword)
        if hit:
            wiki_data.extend(hit)

    if not wiki_data:
        return jsonify({"error": "No Wikipedia data found for the provided keywords"}), 404
    
    wiki_data = clean_duplicate_hits(wiki_data)
    report_es_results(keywords, wiki_data)
    conspiracy_text = gem_consp(GEMINI_API_KEY, keywords, wiki_data)

    return gen_json_output(keywords, conspiracy_text, wiki_data)

# Takes two topics and uses a binary search via shared keywords to find a connection.
# This is recursively repeated until a threshold depth is reached or no more connections are found.
def genV3(es, connected, GEMINI_API_KEY, query, depth=2):
    keywords = [k.strip() for k in query.split(",")]

    if len(keywords) < 2:
        return jsonify({"error": "Please provide at least two keywords for comparison"}), 400
    
    wiki_data = []

    # Take care of info regarding each keyword first
    # Add individual hits for each keyword
    for keyword in keywords:
        hit = esField(es, connected, keyword, "title")
        if hit:
            wiki_data.append(hit[0]) # Assume the first one the desired topic
        else:
            return jsonify({"error": f"⚠️ No hits found for keyword: {keyword} - Exiting Search"}), 400

    # Check for cross-reference hits first
    # Topic1 is start, Topic2 is end
    # Goal is to find suitable middle topic that connects the two
    # returns a tuple ([ hits ], views)

    def cross_ref(topic1, topic2, depth, black_list=[]):
        black_list = black_list.copy()
        black_list.extend([topic1.lower(), topic2.lower()]) # Add current topics to blacklist to avoid repeats

        # End Case (Please STOP!!!)
        if depth <= 0:
            return ([], 0)

        hits = esV2(es, connected, topic1, topic2)

        # Fail Case (No middle topic found)
        if not hits:
            return ([], 0)
        
        # Recursive Case
        sub_hits = [] # Contains tuples with ([start->middle topics], middle topic, [middle->end topics], total topics)
        for hit in hits:
            hit_title = hit['title']

            # Skip if the hit is aready used
            if hit_title.lower() in black_list:
                continue

            # sm and me are both tuples of ([hits], views)
            # start to middle case
            (sm, sm_views) = cross_ref(topic1, hit_title, depth - 1, black_list)
            sm_titles = [t['title'].lower() for t in sm]

            # middle to end case
            (me, me_views) = cross_ref(hit_title, topic2, depth - 1, black_list + sm_titles) # Add start->middle to blacklist

            # Add to list
            # test if views is a number, if not set to 0
            hit_views = hit.get('views', 0) if isinstance(hit.get('views'), int) else 0
            sub_views = sm_views + me_views + hit_views

            sub_len = len(sm) + len(me) + 1
            sub_hits.append((sm, hit, me, sub_len, sub_views))

        # Combine all topics in returned object
        if sub_hits:
            # Sort by total topics (length of sub_hits) and return the one with the most connections
            # Sort Secondary by views (most popular)
            sub_hits.sort(key=lambda x: (x[3], x[4]), reverse=True)

            start = sub_hits[0][0]
            middle = sub_hits[0][1]
            end = sub_hits[0][2]

            # Slap together start, start-middle, middle, middle-end, end topics
            combined_topics = start + [middle] + end

            # Sum Views
            total_views = sub_hits[0][4]

            return (combined_topics, total_views)
        
        # Fails if no sub_hits are found
        # print(f"⚠️ No sub-hits found in cross-ref for {topic1} and {topic2} - Exiting Search")
        return ([], 0)

    (cross_ref_hits, cross_ref_views) = cross_ref(keywords[0], keywords[1], depth)
    if not cross_ref_hits or len(cross_ref_hits) <= 0:
        # iter hits and try to find sub-hits for each one
        return jsonify({"error": "⚠️ No cross-reference hits found - Exiting Search"}), 400
    
    # tag on first and last keywords
    cross_ref_hits = [wiki_data[0]] + cross_ref_hits + [wiki_data[1]]

    print(f"🔍 Cross-reference hits found: {[ch['title'] for ch in cross_ref_hits]}")
    
    # wiki_data = clean_duplicate_hits(wiki_data)
    report_es_results(keywords, cross_ref_hits)
    conspiracy_text = gem_consp(GEMINI_API_KEY, keywords, wiki_data)

    return gen_json_output(keywords, conspiracy_text, wiki_data)