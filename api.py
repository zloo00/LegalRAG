import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import rag_chain

app = FastAPI(title="Legally RAG API", version="1.0")

class ChatRequest(BaseModel):
    query: str

class SourceDocument(BaseModel):
    page_content: str
    metadata: dict

class ChatResponse(BaseModel):
    result: str
    source_documents: List[dict]

import numpy as np

def convert_numpy_types(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    return obj

@app.post("/api/v1/internal-chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Invoke the RAG chain
        response = rag_chain.invoke_qa(request.query)
        
        # Format the response
        result = response.get("result", "")
        source_docs = []
        
        for doc in response.get("source_documents", []):
            if hasattr(doc, "metadata"):
                # Clean metadata of numpy types
                metadata = convert_numpy_types(doc.metadata)
                source_docs.append({
                    "page_content": doc.page_content,
                    "metadata": metadata
                })
            else:
                # Handle case where it might be a dict already or something else
                source_docs.append(convert_numpy_types(doc))

        return ChatResponse(
            result=result,
            source_documents=source_docs
        )
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def get_stats():
    try:
        # Get stats from Pinecone index via LangChain vectorstore
        # Note: This depends on the specific vectorstore implementation
        # For Pinecone, we can access the index directly
        stats = {
            "total_vectors": 0,
            "index_dimension": 0,
            "models": {
                "embedding": "multilingual-e5-large",
                "reranker": "BAAI/bge-reranker-v2-m3" if rag_chain.config.USE_RERANKER else "None"
            }
        }
        
        if hasattr(rag_chain, "_vector_store"):
            # Try to get Pinecone index stats
            try:
                index_stats = rag_chain._vector_store.get_pinecone_index().describe_index_stats()
                stats["total_vectors"] = index_stats.get("total_vector_count", 0)
                stats["index_dimension"] = index_stats.get("dimension", 0)
            except Exception as e:
                print(f"Failed to get Pinecone stats: {e}")
                # Fallback: maybe just return 0 or cached value
        
        return stats
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
