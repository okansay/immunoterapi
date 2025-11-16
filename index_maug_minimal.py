#!/usr/bin/env python3
"""
MAUG Minimal Upload - İlk 10 chunk ile test
Sorun varsa küçük bir örnekle test edin
"""

import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import fitz

from maug_config import MAUG_CHUNKS

load_dotenv()

# Sadece ilk 10 chunk
TEST_CHUNKS = MAUG_CHUNKS[:10]

PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
COLLECTION_NAME = "immunotherapy"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

print(f"🧪 Minimal Test Mode - Sadece {len(TEST_CHUNKS)} chunk")
print(f"   Chunk'lar: {', '.join([c['chunk_id'] for c in TEST_CHUNKS])}")
print("")

# Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)

# PDF aç
print(f"📖 PDF açılıyor: {PDF_PATH}")
doc = fitz.open(PDF_PATH)
print(f"✓ {len(doc)} sayfa")

# Collection kontrol
print(f"\n🗄️  Collection kontrol: {COLLECTION_NAME}")
try:
    qdrant_client.get_collection(COLLECTION_NAME)
    print("✓ Mevcut")
except:
    print("  Oluşturuluyor...")
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE)
    )
    print("✓ Oluşturuldu")

# Upload
print(f"\n🔮 Upload başlıyor...")
for idx, chunk_config in enumerate(TEST_CHUNKS, 1):
    chunk_id = chunk_config["chunk_id"]
    print(f"[{idx}/{len(TEST_CHUNKS)}] {chunk_id}...", end=" ", flush=True)

    # Metin çıkar
    start = chunk_config["start_page"] - 1
    end = chunk_config["end_page"]
    texts = [doc[p].get_text("text") for p in range(start, end) if p < len(doc)]
    text = "\n\n".join(t.strip() for t in texts if t.strip())

    if not text:
        print("⚠️  Boş")
        continue

    # Embedding
    print("emb...", end=" ", flush=True)
    emb = client.embeddings.create(model=EMBEDDING_MODEL, input=text)

    # Upload
    print("up...", end=" ", flush=True)
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=emb.data[0].embedding,
            payload={
                "chunk_id": chunk_id,
                "title": chunk_config["title"],
                "text": text,
                "start_page": chunk_config["start_page"],
                "end_page": chunk_config["end_page"]
            }
        )],
        wait=True
    )
    print("✓")
    time.sleep(0.3)

doc.close()

# Test
print(f"\n🔍 Test araması...")
test_emb = client.embeddings.create(model=EMBEDDING_MODEL, input="allergens")
results = qdrant_client.search(
    collection_name=COLLECTION_NAME,
    query_vector=test_emb.data[0].embedding,
    limit=3
)
for r in results:
    print(f"  - {r.payload['chunk_id']}: {r.payload['title'][:40]}... (score: {r.score:.3f})")

print(f"\n✅ Minimal test başarılı! Tam upload için index_maug_direct.py kullanın.")
