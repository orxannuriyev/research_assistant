from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.validation import ValidationError 
from src.config import Settings
from src.engine import ResearchEngine

# Initialize the FastAPI application
app = FastAPI(title="Research Assistant API", version="1.0")

class ResearchRequest(BaseModel):
    question: str
    sources: str | None = "web, wikipedia, arxiv"  # Default olaraq hamısı seçilir, istifadəçi istəsə dəyişə bilər
    no_cache: bool = False

class CitationResponse(BaseModel):
    index: int
    origin: str
    title: str
    url: str

class ResearchResponse(BaseModel):
    status: str
    question: str
    answer: str | None
    sources_used: list[str]
    citations: list[CitationResponse]
    elapsed_seconds: float

@app.post("/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    try:
        # Initialize settings and research engine
        settings = Settings()
        engine = ResearchEngine(settings=settings)
        
        # Execute the research process directly via the engine
        result = engine.research(
            question=request.question,
            sources=request.sources,
            use_cache=not request.no_cache,
        )
        
        # Extract the AI answer text
        answer_text = (
            result.answer.answer 
            if result.answer else 
            "No answer could be produced because no sources were retrieved."
        )
        
        # Format citations cleanly using Pydantic response objects
        citations = []
        if result.answer and result.answer.citations:
            for citation in result.answer.citations:
                source = citation.source
                citations.append(
                    CitationResponse(
                        index=citation.index,
                        origin=source.origin,
                        title=source.title,
                        url=source.url
                    )
                )
                
        return ResearchResponse(
            status="success",
            question=result.question,
            answer=answer_text,
            sources_used=result.sources_used,
            citations=citations,
            elapsed_seconds=result.elapsed_seconds,
        )
        
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Research provider failed.") from exc