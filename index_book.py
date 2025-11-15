#!/usr/bin/env python3
"""
PDF kitabını chunk'lara böler ve Qdrant'a indexler.
Her chunk GPT-4o-mini ile analiz edilerek chapter bilgisi eklenir.
"""

import os
import time
from typing import List, Dict
from dotenv import load_dotenv
from pypdf import PdfReader
import tiktoken
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

# Load environment variables
load_dotenv()

# Configuration
COLLECTION_NAME = "immunotherapy"
PDF_PATH = "data/book.pdf"
CHUNK_SIZE = 1000  # tokens
CHUNK_OVERLAP = 200  # tokens
BATCH_SIZE = 10  # Qdrant'a aynı anda kaç chunk göndereceğiz
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)
tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Metindeki token sayısını hesaplar."""
    return len(tokenizer.encode(text))


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """PDF'den sayfa sayfa metin çıkarır."""
    print(f"\n📖 PDF okunuyor: {pdf_path}")

    reader = PdfReader(pdf_path)
    pages = []

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            pages.append({
                "page_number": page_num,
                "text": text.strip()
            })
            print(f"  ✓ Sayfa {page_num} okundu ({count_tokens(text)} token)")

    print(f"✓ Toplam {len(pages)} sayfa çıkarıldı")
    return pages


def chunk_text(pages: List[Dict]) -> List[Dict]:
    """Sayfaları chunk'lara böler (overlapping ile)."""
    print(f"\n✂️  Chunk'lara bölünüyor...")

    chunks = []
    current_chunk = ""
    current_chunk_pages = []
    chunk_id = 1

    for page in pages:
        page_text = page["text"]
        page_num = page["page_number"]

        # Metni paragraflara böl
        paragraphs = page_text.split("\n\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Mevcut chunk + yeni paragraf token sayısı
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            tokens = count_tokens(test_chunk)

            if tokens > CHUNK_SIZE and current_chunk:
                # Chunk'ı kaydet
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": current_chunk.strip(),
                    "pages": list(set(current_chunk_pages)),
                    "tokens": count_tokens(current_chunk)
                })
                chunk_id += 1

                # Overlap için son kısmı koru
                sentences = current_chunk.split(". ")
                overlap_text = ". ".join(sentences[-3:]) if len(sentences) > 3 else current_chunk
                overlap_tokens = count_tokens(overlap_text)

                if overlap_tokens < CHUNK_OVERLAP:
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para

                current_chunk_pages = [page_num]
            else:
                current_chunk = test_chunk
                current_chunk_pages.append(page_num)

    # Son chunk'ı ekle
    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_chunk.strip(),
            "pages": list(set(current_chunk_pages)),
            "tokens": count_tokens(current_chunk)
        })

    print(f"✓ Toplam {len(chunks)} chunk oluşturuldu")
    return chunks


def detect_chapter_with_llm(text: str, page_numbers: List[int]) -> Dict[str, str]:
    """
    GPT-4o-mini kullanarak chunk'ın hangi chapter/subsection'a ait olduğunu tespit eder.
    """
    prompt = f"""Aşağıdaki immünoterapi kitabından alınan metin parçasını analiz et.
Bu metnin hangi bölüm (chapter) ve alt başlık (subsection) altında olduğunu tespit et.

Metin:
{text[:500]}... (Sayfa: {', '.join(map(str, page_numbers))})

Lütfen JSON formatında şu bilgileri ver:
{{
    "chapter": "Bölüm adı (örn: 'Introduction to Immunotherapy')",
    "subsection": "Alt başlık (örn: 'T-Cell Activation' veya 'N/A')"
}}

Sadece JSON döndür, başka açıklama yapma."""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Sen immünoterapi kitaplarını analiz eden bir asistansın. Sadece JSON formatında cevap verirsin."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )

        result = response.choices[0].message.content.strip()
        # JSON parse
        import json
        chapter_info = json.loads(result)
        return chapter_info

    except Exception as e:
        print(f"  ⚠️  Chapter detection hatası: {e}")
        return {
            "chapter": f"Page {page_numbers[0]}-{page_numbers[-1]}",
            "subsection": "N/A"
        }


def create_embeddings(chunks: List[Dict]) -> List[Dict]:
    """Chunk'lar için embedding oluşturur ve chapter bilgisi ekler."""
    print(f"\n🔮 Embedding'ler oluşturuluyor ve chapter'lar tespit ediliyor...")

    enriched_chunks = []

    for idx, chunk in enumerate(chunks, 1):
        print(f"  [{idx}/{len(chunks)}] Chunk {chunk['chunk_id']} işleniyor...", end=" ")

        try:
            # 1. Chapter detection (LLM ile)
            chapter_info = detect_chapter_with_llm(
                chunk["text"],
                chunk["pages"]
            )
            print(f"Chapter: {chapter_info['chapter'][:30]}...", end=" ")

            # 2. Embedding oluştur
            emb_response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[chunk["text"]]
            )
            embedding = emb_response.data[0].embedding

            enriched_chunks.append({
                **chunk,
                "chapter": chapter_info["chapter"],
                "subsection": chapter_info["subsection"],
                "embedding": embedding
            })

            print("✓")

            # Rate limiting için kısa bekleme
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Hata: {e}")
            continue

    print(f"✓ {len(enriched_chunks)} chunk hazır")
    return enriched_chunks


def upload_to_qdrant(chunks: List[Dict]):
    """Chunk'ları Qdrant'a yükler."""
    print(f"\n📤 Qdrant'a yükleniyor...")

    points = []
    for chunk in chunks:
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk["embedding"],
            payload={
                "text": chunk["text"],
                "chapter": chunk["chapter"],
                "subsection": chunk["subsection"],
                "pages": chunk["pages"],
                "page": f"{chunk['pages'][0]}-{chunk['pages'][-1]}" if len(chunk['pages']) > 1 else str(chunk['pages'][0]),
                "chunk_id": chunk["chunk_id"],
                "tokens": chunk["tokens"]
            }
        )
        points.append(point)

        # Batch olarak yükle
        if len(points) >= BATCH_SIZE:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"  ✓ {len(points)} chunk yüklendi")
            points = []

    # Kalan chunk'ları yükle
    if points:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"  ✓ {len(points)} chunk yüklendi")

    # Toplam sayıyı göster
    collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    print(f"\n✓ Toplam {collection_info.points_count} chunk Qdrant'ta")


def main():
    """Ana işlem akışı."""
    print("=" * 80)
    print("İMMÜNOTERAPİ KİTABI İNDEXLEME")
    print("=" * 80)

    # PDF'i kontrol et
    if not os.path.exists(PDF_PATH):
        print(f"\n❌ HATA: PDF bulunamadı: {PDF_PATH}")
        print(f"   Lütfen kitabı şu konuma koyun: {os.path.abspath(PDF_PATH)}")
        return

    start_time = time.time()

    # 1. PDF'den metin çıkar
    pages = extract_text_from_pdf(PDF_PATH)

    # 2. Chunk'lara böl
    chunks = chunk_text(pages)

    # 3. Embedding oluştur ve chapter tespit et
    enriched_chunks = create_embeddings(chunks)

    # 4. Qdrant'a yükle
    upload_to_qdrant(enriched_chunks)

    elapsed = time.time() - start_time
    print(f"\n✅ İşlem tamamlandı! Süre: {elapsed:.2f} saniye")
    print(f"📊 İstatistikler:")
    print(f"   - Toplam sayfa: {len(pages)}")
    print(f"   - Toplam chunk: {len(enriched_chunks)}")
    print(f"   - Ortalama chunk boyutu: {sum(c['tokens'] for c in enriched_chunks) / len(enriched_chunks):.0f} token")


if __name__ == "__main__":
    main()
