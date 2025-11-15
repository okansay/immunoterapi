#!/usr/bin/env python3
"""
Gelişmiş PDF indexleme: TOC extraction + Table/Figure koruma
"""

import os
import re
import time
import json
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from pypdf import PdfReader
import tiktoken
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

load_dotenv()

# Configuration
COLLECTION_NAME = "immunotherapy"
PDF_PATH = "data/book.pdf"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
BATCH_SIZE = 10
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
    """Token sayısı"""
    return len(tokenizer.encode(text))


def extract_bookmarks(pdf_path: str) -> Optional[Dict[str, int]]:
    """
    PDF bookmark/outline yapısını okur.
    Returns: {chapter_title: page_number}
    """
    print("\n📑 PDF bookmark'ları okunuyor...")

    try:
        reader = PdfReader(pdf_path)
        outlines = reader.outline

        if not outlines:
            print("  ⚠️  Bookmark bulunamadı")
            return None

        chapters = {}

        def parse_outline(items, level=0):
            for item in items:
                if isinstance(item, list):
                    parse_outline(item, level + 1)
                else:
                    title = item.title if hasattr(item, 'title') else str(item)
                    page = reader.get_destination_page_number(item) + 1  # 1-indexed

                    # Sadece ana başlıkları al (level 0 ve 1)
                    if level <= 1:
                        chapters[title] = page
                        print(f"  ✓ {title} → Sayfa {page}")

        parse_outline(outlines)

        if chapters:
            print(f"✓ {len(chapters)} bookmark bulundu")
            return chapters

    except Exception as e:
        print(f"  ⚠️  Bookmark okuma hatası: {e}")

    return None


def extract_toc_with_llm(reader: PdfReader) -> Optional[Dict[str, int]]:
    """
    PDF'in ilk 20 sayfasını tarayarak TOC (Table of Contents) çıkarır.
    LLM'i sadece 1 kez kullanır.
    """
    print("\n🔍 LLM ile TOC çıkarılıyor...")

    # İlk 20 sayfayı birleştir
    toc_text = ""
    for i in range(min(20, len(reader.pages))):
        page_text = reader.pages[i].extract_text()
        toc_text += f"\n--- SAYFA {i+1} ---\n{page_text}"

    prompt = f"""Aşağıdaki immünoterapi kitabının ilk sayfalarından İçindekiler (Table of Contents) bilgisini çıkar.

{toc_text[:4000]}

Lütfen şu formatta JSON döndür:
{{
    "chapters": [
        {{"title": "Chapter 1: Introduction", "page": 1}},
        {{"title": "Chapter 2: T-Cell Biology", "page": 45}},
        ...
    ]
}}

SADECE JSON döndür, açıklama yapma. İçindekiler bulunamazsa {{"chapters": []}} döndür."""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Sen PDF'lerden Table of Contents çıkaran bir asistansın. Sadece JSON döndürürsün."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )

        result = response.choices[0].message.content.strip()

        # JSON parse
        # Markdown code block varsa temizle
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        data = json.loads(result)

        if not data.get("chapters"):
            print("  ⚠️  TOC bulunamadı")
            return None

        chapters = {}
        for item in data["chapters"]:
            title = item["title"]
            page = int(item["page"])
            chapters[title] = page
            print(f"  ✓ {title} → Sayfa {page}")

        print(f"✓ {len(chapters)} chapter bulundu (LLM)")
        return chapters

    except Exception as e:
        print(f"  ❌ TOC extraction hatası: {e}")
        return None


def get_chapter_mapping(pdf_path: str) -> Dict[int, Tuple[str, str]]:
    """
    Sayfa numarası → (chapter, subsection) mapping oluşturur.
    Returns: {page_num: (chapter_title, subsection_title)}
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    # 1. Önce bookmark'ları dene
    toc = extract_bookmarks(pdf_path)

    # 2. Bookmark yoksa LLM ile TOC çıkar
    if not toc:
        toc = extract_toc_with_llm(reader)

    # 3. Hiçbiri yoksa basit sayfa bazlı isimlendirme
    if not toc:
        print("\n⚠️  TOC bulunamadı, sayfa bazlı isimlendirme yapılacak")
        mapping = {}
        for page_num in range(1, total_pages + 1):
            mapping[page_num] = (f"Section {((page_num-1)//20)+1}", "N/A")
        return mapping

    # TOC'u sayfa aralıklarına çevir
    sorted_chapters = sorted(toc.items(), key=lambda x: x[1])
    mapping = {}

    for i, (chapter_title, start_page) in enumerate(sorted_chapters):
        # Chapter'ın bitiş sayfası = sonraki chapter'ın başlangıcı - 1
        end_page = sorted_chapters[i+1][1] - 1 if i < len(sorted_chapters) - 1 else total_pages

        # Bu aralıktaki tüm sayfalara chapter'ı ata
        for page_num in range(start_page, end_page + 1):
            mapping[page_num] = (chapter_title, "N/A")

    # Boş kalan sayfalar için (TOC öncesi)
    for page_num in range(1, total_pages + 1):
        if page_num not in mapping:
            mapping[page_num] = ("Preface", "N/A")

    print(f"\n✓ {total_pages} sayfa için chapter mapping oluşturuldu")
    return mapping


def is_table_or_figure(text: str) -> bool:
    """
    Metnin tablo veya şekil olup olmadığını tespit eder.
    """
    # Tablo/şekil pattern'leri
    patterns = [
        r'^Table\s+\d+',
        r'^Figure\s+\d+',
        r'^Fig\.\s+\d+',
        r'^Tablo\s+\d+',
        r'^Şekil\s+\d+',
    ]

    for pattern in patterns:
        if re.search(pattern, text.strip(), re.IGNORECASE | re.MULTILINE):
            return True

    # Satır sayısı az ama sütun benzeri yapı varsa (tablo olabilir)
    lines = text.strip().split('\n')
    if len(lines) > 3:
        # Her satırda tab veya çok fazla boşluk varsa
        tab_count = sum(1 for line in lines if '\t' in line or '   ' in line)
        if tab_count / len(lines) > 0.5:
            return True

    return False


def smart_chunk_pages(pages: List[Dict], chapter_mapping: Dict[int, Tuple[str, str]]) -> List[Dict]:
    """
    Sayfaları akıllıca chunk'lar:
    - Chapter değişiminde chunk'ı kır
    - Tablo/şekilleri bütün tut
    - Overlapping uygula
    """
    print(f"\n✂️  Akıllı chunking yapılıyor...")

    chunks = []
    current_chunk = ""
    current_pages = []
    current_chapter = None
    chunk_id = 1

    for page in pages:
        page_num = page["page_number"]
        page_text = page["text"]
        chapter, subsection = chapter_mapping.get(page_num, ("Unknown", "N/A"))

        # Chapter değişti mi?
        if current_chapter and current_chapter != chapter and current_chunk:
            # Mevcut chunk'ı kaydet (chapter sınırında kır)
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "pages": list(set(current_pages)),
                "chapter": current_chapter,
                "subsection": subsection,
                "tokens": count_tokens(current_chunk),
                "type": "chapter_boundary"
            })
            chunk_id += 1
            current_chunk = ""
            current_pages = []

        current_chapter = chapter

        # Sayfa metnini paragraflara böl
        paragraphs = page_text.split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Tablo/şekil kontrolü
            is_special = is_table_or_figure(para)

            # Test: mevcut chunk + yeni paragraf
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            tokens = count_tokens(test_chunk)

            # Chunk size aşıldı mı?
            if tokens > CHUNK_SIZE and current_chunk:
                # Mevcut chunk'ı kaydet
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": current_chunk.strip(),
                    "pages": list(set(current_pages)),
                    "chapter": chapter,
                    "subsection": subsection,
                    "tokens": count_tokens(current_chunk),
                    "type": "normal"
                })
                chunk_id += 1

                # Overlap için son kısmı koru
                sentences = current_chunk.split('. ')
                overlap_text = '. '.join(sentences[-3:]) if len(sentences) > 3 else ""

                if is_special:
                    # Tablo/şekil ise overlap kullanma, yeni chunk başlat
                    current_chunk = para
                else:
                    current_chunk = overlap_text + "\n\n" + para if overlap_text else para

                current_pages = [page_num]
            else:
                current_chunk = test_chunk
                current_pages.append(page_num)

    # Son chunk'ı ekle
    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_chunk.strip(),
            "pages": list(set(current_pages)),
            "chapter": current_chapter or "Unknown",
            "subsection": subsection,
            "tokens": count_tokens(current_chunk),
            "type": "final"
        })

    print(f"✓ {len(chunks)} chunk oluşturuldu")

    # İstatistikler
    normal_chunks = sum(1 for c in chunks if c["type"] == "normal")
    boundary_chunks = sum(1 for c in chunks if c["type"] == "chapter_boundary")
    print(f"  - Normal chunks: {normal_chunks}")
    print(f"  - Chapter boundary chunks: {boundary_chunks}")

    return chunks


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

    print(f"✓ {len(pages)} sayfa çıkarıldı")
    return pages


def create_embeddings(chunks: List[Dict]) -> List[Dict]:
    """Chunk'lar için embedding oluşturur."""
    print(f"\n🔮 Embedding'ler oluşturuluyor...")

    enriched_chunks = []

    for idx, chunk in enumerate(chunks, 1):
        print(f"  [{idx}/{len(chunks)}] Chunk {chunk['chunk_id']}: {chunk['chapter'][:40]}...", end=" ")

        try:
            # Embedding oluştur
            emb_response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[chunk["text"]]
            )
            embedding = emb_response.data[0].embedding

            enriched_chunks.append({
                **chunk,
                "embedding": embedding
            })

            print("✓")
            time.sleep(0.3)  # Rate limiting

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
                "tokens": chunk["tokens"],
                "type": chunk.get("type", "normal")
            }
        )
        points.append(point)

        if len(points) >= BATCH_SIZE:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"  ✓ {len(points)} chunk yüklendi")
            points = []

    if points:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"  ✓ {len(points)} chunk yüklendi")

    collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    print(f"\n✓ Toplam {collection_info.points_count} chunk Qdrant'ta")


def main():
    """Ana işlem akışı"""
    print("=" * 80)
    print("AKILLI İMMÜNOTERAPİ KİTABI İNDEXLEME")
    print("TOC Extraction + Table/Figure Koruma")
    print("=" * 80)

    if not os.path.exists(PDF_PATH):
        print(f"\n❌ HATA: PDF bulunamadı: {PDF_PATH}")
        print(f"   Lütfen kitabı şu konuma koyun: {os.path.abspath(PDF_PATH)}")
        return

    start_time = time.time()

    # 1. Chapter mapping oluştur (TOC extraction)
    chapter_mapping = get_chapter_mapping(PDF_PATH)

    # 2. PDF'den metin çıkar
    pages = extract_text_from_pdf(PDF_PATH)

    # 3. Akıllı chunking (chapter-aware, table-safe)
    chunks = smart_chunk_pages(pages, chapter_mapping)

    # 4. Embedding oluştur
    enriched_chunks = create_embeddings(chunks)

    # 5. Qdrant'a yükle
    upload_to_qdrant(enriched_chunks)

    elapsed = time.time() - start_time
    print(f"\n✅ İşlem tamamlandı! Süre: {elapsed:.2f} saniye")
    print(f"📊 İstatistikler:")
    print(f"   - Toplam sayfa: {len(pages)}")
    print(f"   - Toplam chunk: {len(enriched_chunks)}")
    print(f"   - Ortalama chunk boyutu: {sum(c['tokens'] for c in enriched_chunks) / len(enriched_chunks):.0f} token")
    print(f"   - Chapter sayısı: {len(set(chapter_mapping.values()))}")


if __name__ == "__main__":
    main()
