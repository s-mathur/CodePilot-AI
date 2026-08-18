from utils.session_manager import SessionManager
from utils.embedding_model import EmbeddingModel
from utils.helper import load_json, save_json

from tools.semantic_cache_search_faiss import SemanticCacheFAISS

import hashlib
import json
import os


SEMANTIC_CACHE_THRESHOLD = 0.75

_embedding_model = None

def get_embedding_model():

    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()

    return _embedding_model

def delete_caches(session_id):
    cache_file = get_cache_file(session_id)
    if os.path.exists(cache_file):
        os.remove(cache_file)
    index_file = get_semantic_index_file(session_id)
    if os.path.exists(index_file):
        os.remove(index_file)
    semantic_file = get_semantic_data_file(session_id)
    if os.path.exists(semantic_file):
        os.remove(semantic_file)

def get_cache_file(session_id):
    return os.path.join(SessionManager.get_session_path(session_id), "cache", "cache.json")
    
def get_semantic_index_file(session_id):
    return os.path.join(SessionManager.get_session_path(session_id),"cache", "semantic_cache.index")

def get_semantic_data_file(session_id):
    return os.path.join(SessionManager.get_session_path(session_id), "cache", "semantic_cache_metadata.json")

def generate_hash(text):
    return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()

def _load_cache(session_id):
    cache_file = get_cache_file(session_id)
    cache = load_json(cache_file)

    if not cache:
        cache = {}

    if "exact" not in cache:
        cache = {
            "exact": cache
        }

    return cache, cache_file

def _load_semantic_data(session_id):

    metadata_file = get_semantic_data_file(session_id)

    if not os.path.exists(metadata_file):
        return {}
    try:
        with open(metadata_file, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def _save_semantic_metadata(session_id, metadata):

    metadata_file = get_semantic_data_file(session_id)

    with open(metadata_file, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)


def get_exact_cached_response(session_id, question):

    cache, _ = _load_cache(session_id)
    key = generate_hash(question)

    return cache["exact"].get(key)

def get_semantic_cached_response(session_id, question, task=None, threshold=SEMANTIC_CACHE_THRESHOLD):

    semantic_data = _load_semantic_data(session_id)

    if not semantic_data:
        return None

    # Generate query embedding
    embedding_model = get_embedding_model()
    query_vector = embedding_model.generate_embedding(question)

    # cache FAISS index
    index = SemanticCacheFAISS(get_semantic_index_file(session_id))

    results = index.search(query_vector, top_k=5)

    if not results:
        return None

    for result in results:

        index_id = result["index"]
        score = result["score"]

        data = semantic_data.get(str(index_id))
        if not data:
            continue

        if task is not None:
            if data.get("task") != task:
                continue

        if score < threshold:
            continue
        data.update({
            "matched_question": data["question"],
            "similarity": score,
            "similarity_percentage": round(score * 100, 2),
            "task": data.get("task"),
            "cache_type": "similar"
        })
        return data

    return None

def get_cached_response(session_id, question, task=None, threshold=SEMANTIC_CACHE_THRESHOLD):

    # Check Exact Cache
    exact_response = get_exact_cached_response(session_id, question)
    if exact_response is not None:
        exact_response.update({
            "cache_type": "exact",
            "matched_question": question,
            "similarity": 1.0,
            "similarity_percentage": 100.0
        })
        return exact_response

    # Check Semantic Cache
    semantic_response = get_semantic_cached_response(
        session_id=session_id, question=question,
        task=task, threshold=threshold
    )
    if semantic_response:
        return semantic_response
    # Cache Miss
    return None

def save_response(session_id, question, response, task=None):

    # Save Exact Cache
    cache, cache_file = _load_cache(session_id)

    key = generate_hash(question)
    cache["exact"][key] = {
        "response_type": response['response_type'],
        "response": response['response']
    }

    save_json(cache_file, cache)

    # Save Semantic Cache with all the exact cache - it is needed to remove overhead in searching
    embedding_model = get_embedding_model()
    vector = embedding_model.generate_embedding(question)

    # Load separate FAISS cache index
    index = SemanticCacheFAISS(get_semantic_index_file(session_id))

    # Add vector
    index_id = index.add_vector(vector)

    # Save metadata
    metadata = _load_semantic_data(session_id)

    metadata[str(index_id)] = {
        "question": question,
        "response_type": response['response_type'],
        "response": response['response'],
        "task": task
    }

    _save_semantic_metadata(session_id, metadata)