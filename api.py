from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union, Literal
from src.validation import ValidationError 
from src.config import Settings
from src.engine import ResearchEngine

# Initialize the FastAPI application
app = FastAPI(title="Research Assistant API", version="1.0")

class ResearchRequest(BaseModel):
    question: str
    sources: Union[str, List[str], None] = "web, wikipedia, arxiv"  
    language: Optional[Literal["Azərbaycan", "English"]] = "Azərbaycan"  
    llm_provider: Optional[str] = "openai"  # Streamlit-dən gələn sahəni qarşılamaq üçün əlavə olundu
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
    language: Optional[str] = None

@app.post("/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    try:
        settings = Settings()
        engine = ResearchEngine(settings=settings)
        
        # Seçilmiş dilə uyğun olaraq AI üçün təlimatın əlavə edilməsi
        target_question = request.question
        if request.language == "Azərbaycan":
            target_question = f"{request.question}\n\n(Zəhmət olmasa cavabı yalnız Azərbaycan dilində yazın.)"
        elif request.language == "English":
            target_question = f"{request.question}\n\n(Please write the answer in English.)"

        # Tədqiqat prosesinin icrası
        result = engine.research(
            question=target_question,
            sources=request.sources,
            use_cache=not request.no_cache,
        )
        
        # Cavab mətninin təyini
        if result.answer:
            answer_text = result.answer.answer
        else:
            answer_text = (
                "Heç bir mənbə tapılmadıqları üçün cavab yaradıla bilmədi." 
                if request.language == "Azərbaycan" 
                else "No answer could be produced because no sources were retrieved."
            )
        
        # İstinadların formatlanması
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
            elapsed_seconds=result.elapsed_seconds,
            language=request.language
        )
        
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Research provider failed.") from exc