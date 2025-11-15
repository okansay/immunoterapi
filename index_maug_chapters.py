#!/usr/bin/env python3
"""
MAUG PDF'i JSON chunk tanımına göre deterministik olarak böler ve Qdrant'a yükler.

JSON'daki her chunk için:
- start_page ve end_page arasındaki sayfalar çıkarılır
- Embedding oluşturulur
- Qdrant'a yüklenir

GPT kullanılmaz, tamamen deterministik bir işlemdir.
"""

import os
import json
import time
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import fitz  # PyMuPDF
import uuid

# Load environment
load_dotenv()

# Configuration
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
CHUNKS_JSON = "maug_chapters.json"
COLLECTION_NAME = "maug"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 10

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)


def load_chunk_definitions(json_path: str) -> List[Dict]:
    """JSON dosyasından chunk tanımlarını okur."""
    print(f"\n📖 JSON chunk tanımları okunuyor: {json_path}")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON bulunamadı: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    print(f"✓ {len(chunks)} chunk tanımı okundu")

    return chunks


def extract_chunk_from_pdf(pdf_doc: fitz.Document, chunk_def: Dict) -> str:
    """
    PDF'den belirtilen sayfa aralığındaki metni çıkarır.

    Args:
        pdf_doc: PyMuPDF Document objesi
        chunk_def: {chunk_id, title, start_page, end_page, ...}

    Returns:
        Chunk metni
    """
    start_page = chunk_def["start_page"]
    end_page = chunk_def["end_page"]

    # PyMuPDF 0-indexed, JSON'daki sayfalar 1-indexed
    # start_page=1 → index 0
    pages_text = []

    for page_num in range(start_page - 1, end_page):  # 0-indexed
        if page_num >= len(pdf_doc):
            print(f"  ⚠️  Sayfa {page_num + 1} PDF'de yok, atlanıyor")
            break

        page = pdf_doc[page_num]
        page_text = page.get_text("text")
        pages_text.append(page_text)

    full_text = "\n\n".join(pages_text).strip()

    return full_text


def create_qdrant_collection(collection_name: str):
    """Qdrant collection'ı oluşturur veya yeniden başlatır."""
    print(f"\n🗄️  Qdrant collection hazırlanıyor: {collection_name}")

    # Mevcut collection'ı sil (varsa)
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
        print(f"  ✓ Eski collection silindi")
    except Exception:
        print(f"  ℹ️  Eski collection bulunamadı (normal)")

    # Yeni collection oluştur
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE
        )
    )

    print(f"✓ Yeni collection oluşturuldu")
    print(f"  - Vector boyutu: {EMBEDDING_DIMENSION}")
    print(f"  - Distance metric: COSINE")


def process_and_upload_chunks(pdf_doc: fitz.Document, chunk_definitions: List[Dict], collection_name: str):
    """
    Her chunk için:
    1. PDF'den metni çıkar
    2. Embedding oluştur
    3. Qdrant'a yükle
    """
    print(f"\n🔮 Chunk'lar işleniyor ve Qdrant'a yükleniyor...")

    total_chunks = len(chunk_definitions)
    points = []

    for idx, chunk_def in enumerate(chunk_definitions, 1):
        chunk_id = chunk_def["chunk_id"]
        title = chunk_def["title"]
        section = chunk_def.get("section", "N/A")
        code = chunk_def.get("code")
        start_page = chunk_def["start_page"]
        end_page = chunk_def["end_page"]

        print(f"  [{idx}/{total_chunks}] {chunk_id} - {title[:50]}...", end=" ")

        try:
            # 1. PDF'den metni çıkar
            chunk_text = extract_chunk_from_pdf(pdf_doc, chunk_def)

            if not chunk_text.strip():
                print("⚠️  Boş chunk, atlanıyor")
                continue

            # 2. Embedding oluştur
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=chunk_text
            )
            embedding = response.data[0].embedding

            # 3. Qdrant point oluştur
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "chunk_id": chunk_id,
                    "section": section,
                    "code": code,
                    "title": title,
                    "start_page": start_page,
                    "end_page": end_page,
                    "page": f"{start_page}-{end_page}" if start_page != end_page else str(start_page),
                    "text": chunk_text,
                    "source": os.path.basename(PDF_PATH),
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split())
                }
            )

            points.append(point)
            print(f"✓ ({len(chunk_text.split())} kelime)")

            # Batch olarak yükle
            if len(points) >= BATCH_SIZE:
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                print(f"    ↳ {len(points)} chunk Qdrant'a yüklendi")
                points = []

            # Rate limiting
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

    print(f"\n✓ Tüm chunk'lar işlendi")


def verify_collection(collection_name: str):
    """Qdrant collection'ı doğrular."""
    print(f"\n✅ Collection doğrulanıyor...")

    collection_info = qdrant_client.get_collection(collection_name=collection_name)

    print(f"✓ Collection: {collection_name}")
    print(f"  - Toplam vektör: {collection_info.vectors_count}")
    print(f"  - Toplam nokta: {collection_info.points_count}")

    # Test search
    print(f"\n🔍 Test araması yapılıyor...")

    try:
        test_query = "What are the main allergens in tree pollen?"
        test_response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=test_query
        )
        test_embedding = test_response.data[0].embedding

        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=test_embedding,
            limit=3
        )

        print(f"✓ Test araması başarılı, {len(search_results)} sonuç bulundu:")
        for i, result in enumerate(search_results, 1):
            payload = result.payload
            print(f"  {i}. {payload['chunk_id']} - {payload['title'][:60]}...")
            print(f"     Sayfa: {payload['page']} | Score: {result.score:.3f}")

    except Exception as e:
        print(f"⚠️  Test araması başarısız: {e}")


def main():
    """Ana işlem akışı"""
    print("=" * 80)
    print("MAUG PDF INDEXING - JSON CHUNK DEFINITIONS")
    print("Deterministik Sayfa Tabanlı Bölme + Embedding + Qdrant Upload")
    print("=" * 80)

    # Dosya kontrolleri
    if not os.path.exists(PDF_PATH):
        print(f"\n❌ HATA: PDF bulunamadı: {PDF_PATH}")
        print(f"   Lütfen PDF'i şu konuma koyun: {os.path.abspath(PDF_PATH)}")
        return

    if not os.path.exists(CHUNKS_JSON):
        print(f"\n❌ HATA: JSON bulunamadı: {CHUNKS_JSON}")
        return

    start_time = time.time()

    # 1. JSON chunk tanımlarını oku
    chunk_definitions = load_chunk_definitions(CHUNKS_JSON)

    if not chunk_definitions:
        print("\n❌ Hiç chunk tanımı bulunamadı!")
        return

    # 2. PDF'i aç
    print(f"\n📖 PDF açılıyor: {PDF_PATH}")
    pdf_doc = fitz.open(PDF_PATH)
    print(f"✓ PDF açıldı - Toplam {len(pdf_doc)} sayfa")

    # 3. Qdrant collection oluştur
    create_qdrant_collection(COLLECTION_NAME)

    # 4. Chunk'ları işle ve yükle
    process_and_upload_chunks(pdf_doc, chunk_definitions, COLLECTION_NAME)

    # 5. PDF'i kapat
    pdf_doc.close()

    # 6. Doğrulama
    verify_collection(COLLECTION_NAME)

    elapsed = time.time() - start_time
    print(f"\n✅ İşlem tamamlandı! Süre: {elapsed:.2f} saniye")
    print(f"📊 Collection: {COLLECTION_NAME}")
    print(f"🔮 Embedding Model: {EMBEDDING_MODEL}")

    # İstatistikler
    print(f"\n📈 Özet:")
    print(f"   - Toplam chunk: {len(chunk_definitions)}")
    print(f"   - PDF sayfaları: {len(pdf_doc)}")
    print(f"   - Chunk tanımı: {CHUNKS_JSON}")


if __name__ == "__main__":
    main()
