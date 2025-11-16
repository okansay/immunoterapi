#!/usr/bin/env python3
"""
MAUG PDF → Qdrant Direct Upload (DEBUG VERSION)
Her adımda detaylı log + progress bar
"""

import os
import sys
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
    sys.exit(1)

from maug_config import MAUG_CHUNKS

load_dotenv()

# Configuration
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
COLLECTION_NAME = "immunotherapy"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 5  # Daha küçük batch (debug için)

# Initialize clients
print("🔌 OpenAI client başlatılıyor...")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("✓ OpenAI client hazır")

print("🔌 Qdrant client başlatılıyor...")
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)
print("✓ Qdrant client hazır")


def extract_chunk_text(pdf_doc, chunk_config: Dict) -> str:
    """Belirtilen sayfa aralığından metin çıkarır."""
    start_page = chunk_config["start_page"] - 1
    end_page = chunk_config["end_page"]

    texts = []
    for page_num in range(start_page, end_page):
        if page_num < len(pdf_doc):
            page = pdf_doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                texts.append(page_text.strip())

    return "\n\n".join(texts)


def prepare_chunks(pdf_path: str) -> List[Dict]:
    """PDF'den tüm chunk'ları çıkarır."""
    print(f"\n📖 PDF okunuyor: {pdf_path}")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"❌ PDF bulunamadı: {pdf_path}")

    print("⏳ PDF açılıyor...")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"✓ PDF açıldı: {total_pages} sayfa")

    print(f"\n✂️  Chunk'lar çıkarılıyor ({len(MAUG_CHUNKS)} chunk)...")

    chunks = []
    for idx, chunk_config in enumerate(MAUG_CHUNKS, 1):
        chunk_id = chunk_config["chunk_id"]
        title = chunk_config["title"]
        start_page = chunk_config["start_page"]
        end_page = chunk_config["end_page"]

        print(f"  [{idx}/{len(MAUG_CHUNKS)}] {chunk_id}: {title[:40]}...", end=" ", flush=True)

        # Metin çıkar
        text = extract_chunk_text(doc, chunk_config)

        if not text.strip():
            print("⚠️  Boş chunk!")
            continue

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
    """Collection'un var olduğundan emin olur."""
    print(f"\n🗄️  Collection kontrol ediliyor: {collection_name}")

    try:
        collection_info = qdrant_client.get_collection(collection_name=collection_name)
        print(f"✓ Collection mevcut (mevcut vektör: {collection_info.vectors_count})")
        print(f"⚠️  Yeni chunk'lar mevcut collection'a eklenecek.")
    except Exception as e:
        print(f"  ℹ️  Collection bulunamadı, oluşturuluyor...")
        print(f"     Hata detayı: {e}")

        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )

        print(f"✓ Collection oluşturuldu")


def create_embeddings_and_upload(chunks: List[Dict], collection_name: str):
    """Her chunk için embedding oluşturur ve Qdrant'a yükler."""
    print(f"\n🔮 Embedding'ler oluşturuluyor ve Qdrant'a yükleniyor...")
    print(f"   Toplam: {len(chunks)} chunk")
    print(f"   Batch boyutu: {BATCH_SIZE}")
    print(f"   Tahmin edilen süre: ~{len(chunks) * 0.5 / 60:.1f} dakika")
    print("")

    total_chunks = len(chunks)
    points = []
    uploaded_count = 0
    failed_count = 0

    for idx, chunk in enumerate(chunks, 1):
        chunk_id = chunk["chunk_id"]
        title = chunk["title"]

        print(f"  [{idx}/{total_chunks}] {chunk_id}: {title[:35]}...", end=" ", flush=True)

        try:
            # 1. Embedding oluştur
            print("(emb)", end=" ", flush=True)
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=chunk["text"],
                timeout=30.0  # 30 saniye timeout
            )
            embedding = response.data[0].embedding
            print("✓", end=" ", flush=True)

            # 2. Point oluştur
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "section": chunk["section"],
                    "code": chunk["code"],
                    "chapter": chunk["title"],
                    "subsection": "N/A",
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "start_page": chunk["start_page"],
                    "end_page": chunk["end_page"],
                    "page": f"{chunk['start_page']}-{chunk['end_page']}",
                    "pages": list(range(chunk["start_page"], chunk["end_page"] + 1)),
                    "page_count": chunk["page_count"],
                    "char_count": chunk["char_count"],
                    "word_count": chunk["word_count"],
                    "source": "MAUG_2_20221214_EBOOK.pdf"
                }
            )

            points.append(point)
            uploaded_count += 1
            print("(queue)")

            # Batch upload
            if len(points) >= BATCH_SIZE:
                print(f"\n    ↳ Qdrant'a {len(points)} chunk yükleniyor...", end=" ", flush=True)
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points,
                    wait=True  # Upload tamamlanana kadar bekle
                )
                print("✓")
                points = []

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"❌")
            print(f"      Hata detayı: {e}")
            failed_count += 1
            continue

    # Kalan chunk'ları yükle
    if points:
        print(f"\n    ↳ Son {len(points)} chunk yükleniyor...", end=" ", flush=True)
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )
        print("✓")

    print(f"\n✓ Upload tamamlandı:")
    print(f"   Başarılı: {uploaded_count}/{total_chunks}")
    print(f"   Başarısız: {failed_count}/{total_chunks}")


def verify_upload(collection_name: str):
    """Yüklemeyi doğrular."""
    print(f"\n✅ Doğrulama yapılıyor...")

    try:
        collection_info = qdrant_client.get_collection(collection_name=collection_name)
        print(f"✓ Collection: {collection_name}")
        print(f"  - Toplam vektör: {collection_info.vectors_count}")
        print(f"  - Toplam nokta: {collection_info.points_count}")

        # Test search
        print(f"\n🔍 Test araması...")
        test_query = "What are pollen allergens?"

        print(f"   Sorgu: '{test_query}'")
        print(f"   Embedding oluşturuluyor...", end=" ", flush=True)
        test_response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=test_query
        )
        test_embedding = test_response.data[0].embedding
        print("✓")

        print(f"   Qdrant'ta arama yapılıyor...", end=" ", flush=True)
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=test_embedding,
            limit=3
        )
        print(f"✓ ({len(search_results)} sonuç)")

        for i, result in enumerate(search_results, 1):
            chunk_id = result.payload.get("chunk_id", "N/A")
            title = result.payload.get("title", "N/A")
            score = result.score
            print(f"      {i}. [{chunk_id}] {title[:40]}... (score: {score:.3f})")

    except Exception as e:
        print(f"⚠️  Doğrulama hatası: {e}")


def main():
    """Ana işlem akışı"""
    print("=" * 80)
    print("MAUG PDF → QDRANT UPLOAD (DEBUG VERSION)")
    print("Detaylı log + Her adım izlenir")
    print("=" * 80)

    start_time = time.time()

    try:
        # 1. PDF'den chunk'ları çıkar
        chunks = prepare_chunks(PDF_PATH)

        if not chunks:
            print("\n❌ Hiç chunk çıkarılamadı!")
            sys.exit(1)

        # İstatistikler
        total_words = sum(c["word_count"] for c in chunks)
        avg_words = total_words / len(chunks)

        print(f"\n📊 İstatistikler:")
        print(f"   - Toplam chunk: {len(chunks)}")
        print(f"   - Toplam kelime: {total_words:,}")
        print(f"   - Ortalama: {avg_words:.0f} kelime/chunk")

        # 2. Collection
        ensure_collection(COLLECTION_NAME)

        # 3. Upload
        create_embeddings_and_upload(chunks, COLLECTION_NAME)

        # 4. Verify
        verify_upload(COLLECTION_NAME)

        elapsed = time.time() - start_time
        print(f"\n✅ İşlem tamamlandı!")
        print(f"   Süre: {elapsed:.2f} saniye ({elapsed/60:.1f} dakika)")
        print(f"   Collection: {COLLECTION_NAME}")

    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem kullanıcı tarafından durduruldu!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ HATA: {e}")
        import traceback
        print("\nDetaylı hata:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
