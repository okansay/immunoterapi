#!/usr/bin/env python3
"""
MAUG PDF → Qdrant Direct Upload
Predefined chunk mapping ile direkt upload (LLM'siz)
"""

import os
import time
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF kurulu değil!")
    print("Kurulum: pip install PyMuPDF")
    exit(1)

# Konfigürasyonu import et
from maug_config import MAUG_CHUNKS

# Load environment
load_dotenv()

# Configuration
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
COLLECTION_NAME = "immunotherapy"  # Ana collection adınız
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 10

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)


def extract_chunk_text(pdf_doc, chunk_config: Dict) -> str:
    """
    Belirtilen sayfa aralığından metin çıkarır.

    Args:
        pdf_doc: PyMuPDF document object
        chunk_config: MAUG_CHUNKS'tan bir item

    Returns:
        Chunk metni
    """
    start_page = chunk_config["start_page"] - 1  # 0-indexed
    end_page = chunk_config["end_page"]  # exclusive

    texts = []
    for page_num in range(start_page, end_page):
        if page_num < len(pdf_doc):
            page = pdf_doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                texts.append(page_text.strip())

    return "\n\n".join(texts)


def prepare_chunks(pdf_path: str) -> List[Dict]:
    """
    PDF'den tüm chunk'ları çıkarır.

    Returns:
        List of chunks with text and metadata
    """
    print(f"\n📖 PDF okunuyor: {pdf_path}")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"❌ PDF bulunamadı: {pdf_path}")

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"✓ PDF açıldı: {total_pages} sayfa")

    print(f"\n✂️  Chunk'lar çıkarılıyor...")

    chunks = []
    for idx, chunk_config in enumerate(MAUG_CHUNKS, 1):
        chunk_id = chunk_config["chunk_id"]
        title = chunk_config["title"]
        start_page = chunk_config["start_page"]
        end_page = chunk_config["end_page"]

        print(f"  [{idx}/{len(MAUG_CHUNKS)}] {chunk_id}: {title[:50]}...", end=" ")

        # Metin çıkar
        text = extract_chunk_text(doc, chunk_config)

        if not text.strip():
            print("⚠️  Boş chunk!")
            continue

        # Chunk oluştur
        chunk = {
            "chunk_id": chunk_id,
            "section": chunk_config["section"],
            "code": chunk_config["code"],
            "title": title,
            "text": text,
            "start_page": start_page,
            "end_page": end_page,
            "page_count": end_page - start_page + 1,
            "char_count": len(text),
            "word_count": len(text.split())
        }

        chunks.append(chunk)
        print(f"✓ ({chunk['word_count']} kelime)")

    doc.close()

    print(f"\n✓ Toplam {len(chunks)} chunk hazır")
    return chunks


def ensure_collection(collection_name: str):
    """
    Collection'un var olduğundan emin olur. Yoksa oluşturur.
    """
    print(f"\n🗄️  Collection kontrol ediliyor: {collection_name}")

    try:
        # Collection var mı?
        collection_info = qdrant_client.get_collection(collection_name=collection_name)
        print(f"✓ Collection mevcut")
        print(f"  - Mevcut vektör sayısı: {collection_info.vectors_count}")

        # Kullanıcıya sor
        print(f"\n⚠️  Bu işlem mevcut collection'a yeni chunk'lar ekleyecek.")
        print(f"   Devam edilsin mi? (y/n): ", end="")

        # Auto-continue for non-interactive mode
        if os.getenv("AUTO_CONTINUE"):
            print("y (auto)")
            return

        response = input().strip().lower()
        if response != "y":
            print("❌ İşlem iptal edildi")
            exit(0)

    except Exception:
        # Collection yok, oluştur
        print(f"  ℹ️  Collection bulunamadı, oluşturuluyor...")

        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )

        print(f"✓ Collection oluşturuldu")
        print(f"  - Vector boyutu: {EMBEDDING_DIMENSION}")
        print(f"  - Distance metric: COSINE")


def create_embeddings_and_upload(chunks: List[Dict], collection_name: str):
    """
    Her chunk için embedding oluşturur ve Qdrant'a yükler.
    """
    print(f"\n🔮 Embedding'ler oluşturuluyor ve Qdrant'a yükleniyor...")

    total_chunks = len(chunks)
    points = []
    uploaded_count = 0

    for idx, chunk in enumerate(chunks, 1):
        chunk_id = chunk["chunk_id"]
        title = chunk["title"]

        print(f"  [{idx}/{total_chunks}] {chunk_id}: {title[:40]}...", end=" ")

        try:
            # 1. Embedding oluştur
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=chunk["text"]
            )
            embedding = response.data[0].embedding

            # 2. Qdrant point oluştur
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "section": chunk["section"],
                    "code": chunk["code"],
                    "chapter": chunk["title"],  # "chapter" field for consistency with main.py
                    "subsection": "N/A",  # Compatibility
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "start_page": chunk["start_page"],
                    "end_page": chunk["end_page"],
                    "page": f"{chunk['start_page']}-{chunk['end_page']}",  # Compatibility
                    "pages": list(range(chunk["start_page"], chunk["end_page"] + 1)),  # Compatibility
                    "page_count": chunk["page_count"],
                    "char_count": chunk["char_count"],
                    "word_count": chunk["word_count"],
                    "source": "MAUG_2_20221214_EBOOK.pdf"
                }
            )

            points.append(point)
            uploaded_count += 1
            print("✓")

            # Batch olarak yükle
            if len(points) >= BATCH_SIZE:
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                print(f"    ↳ {len(points)} chunk Qdrant'a yüklendi")
                points = []

            # Rate limiting (OpenAI API için)
            time.sleep(0.3)

        except Exception as e:
            print(f"❌ Hata: {e}")
            continue

    # Kalan chunk'ları yükle
    if points:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"    ↳ {len(points)} chunk Qdrant'a yüklendi")

    print(f"\n✓ {uploaded_count}/{total_chunks} chunk başarıyla yüklendi")


def verify_upload(collection_name: str):
    """
    Yüklemeyi doğrular ve test araması yapar.
    """
    print(f"\n✅ Yükleme doğrulanıyor...")

    try:
        collection_info = qdrant_client.get_collection(collection_name=collection_name)

        print(f"✓ Collection: {collection_name}")
        print(f"  - Toplam vektör: {collection_info.vectors_count}")
        print(f"  - Toplam nokta: {collection_info.points_count}")

        # Test search
        print(f"\n🔍 Test araması yapılıyor...")

        test_queries = [
            "What are pollen allergens?",
            "Milk allergy components",
            "Basophil activation test"
        ]

        for query in test_queries:
            print(f"\n  Sorgu: '{query}'")

            # Embedding oluştur
            test_response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=query
            )
            test_embedding = test_response.data[0].embedding

            # Arama yap
            search_results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=test_embedding,
                limit=3,
                score_threshold=0.5
            )

            if search_results:
                print(f"  ✓ {len(search_results)} sonuç:")
                for i, result in enumerate(search_results, 1):
                    chunk_id = result.payload.get("chunk_id", "N/A")
                    title = result.payload.get("title", "N/A")
                    score = result.score

                    print(f"    {i}. [{chunk_id}] {title[:50]}... (score: {score:.3f})")
            else:
                print(f"  ⚠️  Sonuç bulunamadı")

    except Exception as e:
        print(f"⚠️  Doğrulama hatası: {e}")


def main():
    """Ana işlem akışı"""
    print("=" * 80)
    print("MAUG PDF → QDRANT DIRECT UPLOAD")
    print("Predefined Chunks + Embedding + Vector Database")
    print("=" * 80)

    start_time = time.time()

    # 1. PDF'den chunk'ları çıkar
    chunks = prepare_chunks(PDF_PATH)

    if not chunks:
        print("\n❌ Hiç chunk çıkarılamadı!")
        return

    # İstatistikler
    total_words = sum(c["word_count"] for c in chunks)
    avg_words = total_words / len(chunks)

    print(f"\n📊 İstatistikler:")
    print(f"   - Toplam chunk: {len(chunks)}")
    print(f"   - Toplam kelime: {total_words:,}")
    print(f"   - Ortalama chunk uzunluğu: {avg_words:.0f} kelime")
    print(f"   - En kısa chunk: {min(c['word_count'] for c in chunks)} kelime")
    print(f"   - En uzun chunk: {max(c['word_count'] for c in chunks)} kelime")

    # 2. Collection'u kontrol et/oluştur
    ensure_collection(COLLECTION_NAME)

    # 3. Embedding oluştur ve Qdrant'a yükle
    create_embeddings_and_upload(chunks, COLLECTION_NAME)

    # 4. Yüklemeyi doğrula
    verify_upload(COLLECTION_NAME)

    elapsed = time.time() - start_time
    print(f"\n✅ İşlem tamamlandı! Süre: {elapsed:.2f} saniye ({elapsed/60:.1f} dakika)")
    print(f"📊 Collection: {COLLECTION_NAME}")
    print(f"🔮 Embedding Model: {EMBEDDING_MODEL}")
    print(f"📄 Kaynak: {PDF_PATH}")


if __name__ == "__main__":
    main()
