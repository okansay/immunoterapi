#!/usr/bin/env python3
"""
Immunotherapy Decision Support API
FastAPI backend for RAG-based immunotherapy consultation
"""

import os
import time
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Configuration
COLLECTION_NAME = "maug"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "o1-preview"  # Reasoning model (yavaş ama güçlü)

# Initialize FastAPI
app = FastAPI(
    title="Immunotherapy Decision Support API",
    version="1.0.0",
    description="RAG-based decision support system for immunotherapy"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da domain ile sınırlandırın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
# OpenAI client (for both embeddings and LLM)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Qdrant client
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)


# Pydantic models
class QueryRequest(BaseModel):
    question: str
    language: str = "tr"  # "tr" veya "en"
    top_k: int = 5  # Kaç kaynak döndürülecek
    score_threshold: float = 0.4  # Minimum benzerlik skoru


class SourceInfo(BaseModel):
    chapter: str
    subsection: str
    page: str
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    processing_time: float


# Endpoints
@app.get("/")
async def root():
    """API durum kontrolü"""
    return {
        "message": "Immunotherapy Decision Support API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Sağlık kontrolü - Qdrant bağlantısını test eder"""
    try:
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if COLLECTION_NAME not in collection_names:
            return {
                "status": "unhealthy",
                "error": f"Collection '{COLLECTION_NAME}' not found",
                "available_collections": collection_names
            }

        # Collection bilgisi
        collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)

        return {
            "status": "healthy",
            "qdrant": "connected",
            "collection": COLLECTION_NAME,
            "points_count": collection_info.points_count,
            "vectors_count": collection_info.vectors_count
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/api/query", response_model=QueryResponse)
async def query_immunotherapy(req: QueryRequest):
    """
    İmmünoterapi sorusu sorar ve RAG tabanlı cevap alır.

    Args:
        req: Soru, dil ve arama parametreleri

    Returns:
        QueryResponse: Cevap, kaynaklar ve işlem süresi
    """
    start_time = time.time()

    try:
        # 1. Embedding oluştur
        emb_response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[req.question]
        )
        query_vector = emb_response.data[0].embedding

        # 2. Qdrant'ta ara
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=req.top_k,
            score_threshold=req.score_threshold
        )

        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="İlgili kaynak bulunamadı. Lütfen sorunuzu farklı şekilde ifade edin."
            )

        # 3. Context ve kaynak listesi oluştur
        context_parts = []
        sources = []

        for idx, result in enumerate(search_results, 1):
            context_parts.append(
                f"[Kaynak {idx}]\n"
                f"Bölüm: {result.payload.get('chapter', 'N/A')}\n"
                f"Alt Başlık: {result.payload.get('subsection', 'N/A')}\n"
                f"Sayfa: {result.payload.get('page', 'N/A')}\n\n"
                f"{result.payload['text']}"
            )

            sources.append(SourceInfo(
                chapter=result.payload.get("chapter", "N/A"),
                subsection=result.payload.get("subsection", "N/A"),
                page=result.payload.get("page", "N/A"),
                relevance_score=round(result.score, 3)
            ))

        context = "\n\n---\n\n".join(context_parts)

        # 4. LLM ile cevap oluştur (o1-preview formatı)
        # o1 modelleri system prompt desteklemiyor, tüm prompt user mesajında olmalı
        language_instruction = "Cevabı Türkçe ver." if req.language == "tr" else "Respond in English."

        user_prompt = f"""Sen immünoterapi konusunda uzman bir tıbbi asistansın.
Görevin doktorlara bilimsel kaynaklara dayalı karar destek sağlamaktır.

ÖNEMLİ KURALLAR:
1. Sadece verilen kaynak bilgilerine dayanarak cevap ver
2. Bilimsel ve net bir dil kullan
3. Emin olmadığın konularda bunu açıkça belirt
4. Gerekirse kaynak numaralarına referans ver (örn: "Kaynak 1'e göre...")
5. Tıbbi önerilerde bulunurken dikkatli ol, sadece bilgilendirici ol
6. {language_instruction}

{'=' * 80}

Kaynak bilgiler:

{context}

{'=' * 80}

Soru: {req.question}

Lütfen yukarıdaki kaynaklara dayanarak detaylı ve bilimsel bir cevap ver."""

        # o1-preview ile cevap oluştur (system prompt yok, temperature yok)
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        answer = completion.choices[0].message.content

        processing_time = time.time() - start_time

        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time=round(processing_time, 3)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"İşlem sırasında hata oluştu: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))

    print("=" * 80)
    print("IMMUNOTHERAPY DECISION SUPPORT API")
    print("=" * 80)
    print(f"🚀 Starting server on {host}:{port}")
    print(f"📚 Collection: {COLLECTION_NAME}")
    print(f"🔮 Embedding Model: {EMBEDDING_MODEL}")
    print(f"🤖 LLM Model: {LLM_MODEL}")
    print("=" * 80)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )
