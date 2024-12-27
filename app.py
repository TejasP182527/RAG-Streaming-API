__author__ = "Tejas Pathak"
__version__ = "1.0"
__description__ = "This is a FastAPI application for RAG Streaming API. It processes user queries and returns relevant context based on predefined mock data."
__app_name__ = "RAG Streaming API - Karini Lab Test"

# Importing required libraries
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import time
import asyncio
from typing import List, Optional
from data import mock_data
from entities import topic_keywords

# Initialize the FastAPI app
app = FastAPI(title="RAG Streaming API")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the request model
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3  # Default value for top_k if not provided

# Function to retrieve context based on the query and top_k
def get_relevant_context(query: str, top_k: int) -> List[str]:
    relevant_sentences = []
    query_lower = query.lower()

    # Identify the topic that is most relevant to the query
    matched_topic = None
    for topic, context in mock_data.items():
        if any(keyword.lower() in query_lower for keyword in topic_keywords.get(topic, [])):
            matched_topic = topic
            break

    if not matched_topic:
        logger.info(f"No relevant topic found for query: {query}")
        return []

    matched_keywords = set(keyword.lower() for keyword in topic_keywords[matched_topic])
    relevant_sentences = [sentence for sentence in mock_data[matched_topic] 
                          if any(keyword in sentence.lower() for keyword in matched_keywords)]

    return relevant_sentences[:top_k]

# Function for the streaming response
def generate_streaming_response(query: str, top_k: int):
    context = get_relevant_context(query, top_k)
    logger.info(f"Generating response for query: '{query}' with top_k={top_k}")
    
    if not context:
        raise HTTPException(status_code=404, detail="No relevant context found")
    response_content = "\n".join(context) + "\n"
    yield response_content
    time.sleep(1)

# API endpoint to handle user queries
@app.post("/query")
async def query_endpoint(request: QueryRequest):
    logger.info(f"Received query: {request.query}")
    
    try:
        return StreamingResponse(generate_streaming_response(request.query, request.top_k), media_type="text/plain")
    
    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Error processing the query: {e}")
        logger.error(f"Error processing the query '{request.query}' with top_k={request.top_k}: {e}")
