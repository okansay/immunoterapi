#!/usr/bin/env python3
"""
MAUG Chunks'ları Qdrant'a Yükler
JSONL → Embedding → Qdrant Vector Database
"""

import os
import json
import time
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

# Load environment
load_dotenv()

# Configuration
JSONL_PATH = "maug_chunks.jsonl"
COLLECTION_NAME = "maug"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small dimension
BATCH_SIZE = 10  # Qdrant'a aynı anda kaç chunk yüklenecek

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)


def load_chunks_from_jsonl(jsonl_path: str) -> List[Dict]:
    """JSONL dosyasından chunk'ları okur."""
    print(f"\n📖 JSONL okunuyor: {jsonl_path}")

    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"JSONL bulunamadı: {jsonl_path}")

    chunks = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                chunk = json.loads(line)
                chunks.append(chunk)
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Satır {line_num} parse edilemedi: {e}")
                continue

    print(f"✓ {len(chunks)} chunk okundu")
    return chunks


def create_collection(collection_name: str):
    """Qdrant'ta yeni collection oluşturur."""
    print(f"\n🗄️  Collection oluşturuluyor: {collection_name}")

    # Mevcut collection'u sil (varsa)
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

    for idx, chunk in enumerate(chunks, 1):
        print(f"  [{idx}/{total_chunks}] {chunk['id']} - {chunk['chapter_id']}...", end=" ")

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
                    "id": chunk["id"],
                    "chapter_id": chunk["chapter_id"],
                    "chapter_title": chunk["chapter_title"],
                    "segment_index": chunk["segment_index"],
                    "text": chunk["text"],
                    "start_page": chunk.get("start_page"),
                    "end_page": chunk.get("end_page"),
                    "source": chunk["source"]
                }
            )

            points.append(point)
            print("✓")

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

    print(f"\n✓ Tüm chunk'lar yüklendi")


def verify_upload(collection_name: str):
    """Qdrant'a yüklemeyi doğrular."""
    print(f"\n✅ Yükleme doğrulanıyor...")

    collection_info = qdrant_client.get_collection(collection_name=collection_name)

    print(f"✓ Collection: {collection_name}")
    print(f"  - Toplam vektör: {collection_info.vectors_count}")
    print(f"  - Toplam nokta: {collection_info.points_count}")

    # Test search
    print(f"\n🔍 Test araması yapılıyor...")

    try:
        # Rastgele bir sorgu embedding'i oluştur
        test_query = "What are the main allergens in pollen?"
        test_response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=test_query
        )
        test_embedding = test_response.data[0].embedding

        # Arama yap
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=test_embedding,
            limit=3
        )

        print(f"✓ Test araması başarılı, {len(search_results)} sonuç bulundu:")
        for i, result in enumerate(search_results, 1):
            print(f"  {i}. {result.payload['id']} - {result.payload['chapter_title'][:50]}...")
            print(f"     Score: {result.score:.3f}")

    except Exception as e:
        print(f"⚠️  Test araması başarısız: {e}")


def main():
    """Ana işlem akışı"""
    print("=" * 80)
    print("MAUG CHUNKS → QDRANT UPLOAD")
    print("Embedding + Vector Database Upload")
    print("=" * 80)

    start_time = time.time()

    # 1. JSONL'den chunk'ları oku
    chunks = load_chunks_from_jsonl(JSONL_PATH)

    if not chunks:
        print("\n❌ Hiç chunk bulunamadı!")
        return

    # 2. Qdrant collection oluştur
    create_collection(COLLECTION_NAME)

    # 3. Embedding oluştur ve yükle
    create_embeddings_and_upload(chunks, COLLECTION_NAME)

    # 4. Yüklemeyi doğrula
    verify_upload(COLLECTION_NAME)

    elapsed = time.time() - start_time
    print(f"\n✅ İşlem tamamlandı! Süre: {elapsed:.2f} saniye")
    print(f"📊 Collection: {COLLECTION_NAME}")
    print(f"🔮 Embedding Model: {EMBEDDING_MODEL}")


if __name__ == "__main__":
    main()
