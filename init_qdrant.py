#!/usr/bin/env python3
"""
Qdrant koleksiyonunu oluşturur ve yapılandırır.
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load environment variables
load_dotenv()

COLLECTION_NAME = "immunotherapy"
VECTOR_SIZE = 1536  # text-embedding-3-small model size

def init_collection():
    """Qdrant koleksiyonunu oluşturur."""

    # Qdrant client
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))

    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # Koleksiyon varsa sil (isteğe bağlı)
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✓ Eski koleksiyon silindi: {COLLECTION_NAME}")
    except Exception as e:
        print(f"ℹ Eski koleksiyon bulunamadı (normal): {e}")

    # Yeni koleksiyon oluştur
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )

    print(f"✓ Yeni koleksiyon oluşturuldu: {COLLECTION_NAME}")
    print(f"  - Vector boyutu: {VECTOR_SIZE}")
    print(f"  - Distance metric: COSINE")

    # Koleksiyon bilgilerini göster
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"\nKoleksiyon durumu:")
    print(f"  - Toplam nokta sayısı: {collection_info.points_count}")
    print(f"  - Vector sayısı: {collection_info.vectors_count}")

if __name__ == "__main__":
    print("=" * 60)
    print("QDRANT KOLEKSİYON BAŞLATMA")
    print("=" * 60)
    init_collection()
    print("\n✅ İşlem tamamlandı!")
