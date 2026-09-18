from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.config import Settings
from src.engine import ResearchEngine
from src.validation import normalize_sources

# Initialize the FastAPI application
app = FastAPI(title="Research Assistant API", version="1.0")

class ResearchRequest(BaseModel):
    question: str
    sources: str | None = None
    no_cache: bool = False

@app.post("/research")
def run_research(request: ResearchRequest):
    try:
        # Initialize settings and research engine
        settings = Settings()
        engine = ResearchEngine(settings=settings)
        
        # Normalize sources using project validation
        normalized_sources = normalize_sources(request.sources)
        
        # Execute the research process
        result = engine.research(
            question=request.question,
            sources=normalized_sources,
            use_cache=not request.no_cache,
        )
        
        # Extract the AI answer text
        answer_text = (
            result.answer.answer 
            if result.answer else 
            "No answer could be produced because no sources were retrieved."
        )
        
        # Format citations cleanly
        citations = []
        if result.answer and result.answer.citations:
            for citation in result.answer.citations:
                source = citation.source
                citations.append({
                    "index": citation.index,
                    "origin": source.origin,
                    "title": source.title,
                    "url": source.url
                })
                
        return {
            "status": "success",
            "question": request.question,
            "answer": answer_text,
            "sources_used": result.sources_used,
            "citations": citations,
            "elapsed_seconds": result.elapsed_seconds
        }
    except Exception as e:
        # Return HTTP 500 error on failure
        raise HTTPException(status_code=500, detail=str(e))