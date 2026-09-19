from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union
from src.validation import ValidationError 
from src.config import Settings
from src.engine import ResearchEngine

# Initialize the FastAPI application
app = FastAPI(title="Research Assistant API", version="1.0")

class ResearchRequest(BaseModel):
    question: str
    sources: Union[str, List[str], None] = "web, wikipedia, arxiv"  
    llm_provider: Optional[str] = "openai"  
    no_cache: bool = False

    @field_validator("sources", mode="before")
    @classmethod
    def parse_sources(cls, v):
        if isinstance(v, list):
            return ", ".join(v)
        return v

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
        settings = Settings()
        
        # Override the LLM provider with the one selected from Streamlit UI
        if request.llm_provider:
            settings.llm_provider = request.llm_provider

        engine = ResearchEngine(settings=settings)
        
        target_question = request.question

        # Execute the research process
        result = engine.research(
            question=target_question,
            sources=request.sources,
            use_cache=not request.no_cache,
        )
        
        # Determine the answer text
        if result.answer:
            answer_text = result.answer.answer
        else:
            answer_text = "No answer could be produced because no sources were retrieved."
        
        # Format citations
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
            question=request.question,
            answer=answer_text,
            sources_used=result.sources_used,
            citations=citations,
            elapsed_seconds=result.elapsed_seconds
        )
        
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc) or "Research provider failed.") from exc
