#!/usr/bin/env python3
"""
MAUG (Molecular Allergology User's Guide) PDF Chunking Pipeline

İki katmanlı yaklaşım:
1. Deterministik katman: PDF → metin + chapter tespiti (regex)
2. LLM katmanı: Her chapter → mantıklı segmentlere bölme (GPT-4o-mini)

Çıktı: JSONL formatında chapter-aware, table-safe chunk'lar
"""

import os
import re
import json
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import fitz  # PyMuPDF

# Load environment
load_dotenv()

# Configuration
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
OUTPUT_JSONL = "maug_chunks.jsonl"
LLM_MODEL = "gpt-4o-mini"

# Segmentation parameters
MIN_CHARS = 2000   # Minimum segment uzunluğu (karakter)
MAX_CHARS = 8000   # Maximum segment uzunluğu (karakter)
TARGET_WORDS = 800  # Hedef kelime sayısı (500-1500 arası)

# Chapter pattern: A01, B02, C11, D03 gibi
CHAPTER_PATTERN = re.compile(
    r"^([ABCD]\d{2})\s*[–-]\s*(.+)$",
    flags=re.MULTILINE
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_with_page_markers(pdf_path: str) -> str:
    """
    PDF'ten metin çıkarır ve her sayfaya [[PAGE_X]] marker ekler.

    Returns:
        Full text with page markers
    """
    print(f"\n📖 PDF okunuyor: {pdf_path}")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF bulunamadı: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc, 1):
        page_text = page.get_text("text")
        # Sayfa marker'ı ekle
        marked_text = f"[[PAGE_{i}]]\n{page_text}"
        pages.append(marked_text)

        if i % 50 == 0:
            print(f"  ✓ {i} sayfa işlendi...")

    full_text = "\n\n".join(pages)

    print(f"✓ Toplam {len(doc)} sayfa çıkarıldı")
    doc.close()

    return full_text


def detect_chapters(full_text: str) -> List[Dict]:
    """
    Regex ile chapter'ları tespit eder.

    Pattern: A01 - Title, B02 – Title, etc.

    Returns:
        List of chapters with id, title, text
    """
    print(f"\n🔍 Chapter'lar tespit ediliyor...")

    matches = list(CHAPTER_PATTERN.finditer(full_text))

    if not matches:
        print("  ⚠️  Hiç chapter bulunamadı!")
        return []

    chapters = []

    # İlk chapter'dan önceki kısım (preface)
    first_match = matches[0]
    if first_match.start() > 100:  # En az 100 karakter varsa
        preface_text = full_text[:first_match.start()].strip()
        if preface_text:
            chapters.append({
                "chapter_id": "PREFACE",
                "chapter_title": "Prefaces and Introduction",
                "text": preface_text
            })
            print(f"  ✓ PREFACE - Prefaces and Introduction")

    # Her chapter için
    for i, match in enumerate(matches):
        chapter_id = match.group(1)  # A01, B02, etc.
        chapter_title = match.group(2).strip()

        start = match.start()
        # Sonraki chapter'ın başlangıcı veya text sonu
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)

        chapter_text = full_text[start:end].strip()

        chapters.append({
            "chapter_id": chapter_id,
            "chapter_title": chapter_title,
            "text": chapter_text
        })

        print(f"  ✓ {chapter_id} - {chapter_title[:60]}...")

    print(f"✓ Toplam {len(chapters)} chapter bulundu")
    return chapters


def segment_chapter_with_llm(chapter: Dict) -> Optional[List[Dict]]:
    """
    GPT-4o-mini ile chapter'ı segmentlere böler.

    Args:
        chapter: {chapter_id, chapter_title, text}

    Returns:
        List of segments: [{local_id, start_snippet, end_snippet}]
    """
    chapter_id = chapter["chapter_id"]
    chapter_title = chapter["chapter_title"]
    chapter_text = chapter["text"]

    # Çok kısa chapter'ları bölme
    word_count = len(chapter_text.split())
    if word_count < 300:
        print(f"    ⚠️  Chapter çok kısa ({word_count} kelime), bölünmeyecek")
        return [{
            "local_id": "01",
            "start_snippet": chapter_text[:60],
            "end_snippet": chapter_text[-60:]
        }]

    # System prompt
    system_prompt = """You are a document segmentation assistant for medical textbooks.

Your task: Split a chapter into 2-8 contiguous segments that preserve topic coherence.

CRITICAL RULES:
1. DO NOT modify or rewrite the text - only decide segment boundaries
2. Prefer splitting at subsection headings (title-like single lines)
3. NEVER split tables or figures - keep lines starting with "Table" or "Figure" together
4. Each segment: 500-1500 words (unless chapter is shorter)
5. Output MUST be valid JSON, no extra text

For each segment return:
- "local_id": zero-padded string ("01", "02", "03"...)
- "start_snippet": EXACT first 40-70 chars of segment
- "end_snippet": EXACT last 40-70 chars of segment

We use snippets to cut the original text, so they MUST match exactly."""

    # User prompt
    user_prompt = f"""Chapter ID: {chapter_id}
Chapter title: {chapter_title}

Text:
\"\"\"
{chapter_text[:12000]}{"..." if len(chapter_text) > 12000 else ""}
\"\"\"

Return JSON in this exact format:

{{
  "segments": [
    {{
      "local_id": "01",
      "start_snippet": "...",
      "end_snippet": "..."
    }},
    {{
      "local_id": "02",
      "start_snippet": "...",
      "end_snippet": "..."
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        response_text = response.choices[0].message.content.strip()

        # JSON temizleme (markdown code block varsa)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Parse JSON
        data = json.loads(response_text)
        segments = data.get("segments", [])

        if not segments:
            raise ValueError("No segments returned")

        print(f"    ✓ {len(segments)} segment önerildi")
        return segments

    except Exception as e:
        print(f"    ❌ LLM segmentation hatası: {e}")
        print(f"    ↳ Fallback: Basit bölme kullanılacak")
        return None


def simple_segmentation_fallback(chapter_text: str, num_segments: int = 3) -> List[Dict]:
    """
    LLM başarısız olursa basit paragraf bazlı bölme.
    """
    paragraphs = [p.strip() for p in chapter_text.split("\n\n") if p.strip()]

    if not paragraphs:
        return [{
            "local_id": "01",
            "start_snippet": chapter_text[:60],
            "end_snippet": chapter_text[-60:]
        }]

    # Paragrafları eşit gruplara böl
    chunk_size = max(1, len(paragraphs) // num_segments)
    segments = []

    for i in range(0, len(paragraphs), chunk_size):
        segment_paras = paragraphs[i:i + chunk_size]
        segment_text = "\n\n".join(segment_paras)

        segments.append({
            "local_id": f"{len(segments) + 1:02d}",
            "start_snippet": segment_text[:60],
            "end_snippet": segment_text[-60:]
        })

    return segments


def extract_segments_from_text(chapter: Dict, llm_segments: List[Dict]) -> List[Dict]:
    """
    LLM'den gelen snippet'lere göre gerçek segment'leri çıkarır.

    Returns:
        List of complete segments with text and metadata
    """
    chapter_id = chapter["chapter_id"]
    chapter_title = chapter["chapter_title"]
    chapter_text = chapter["text"]

    segments = []

    for seg_info in llm_segments:
        local_id = seg_info["local_id"]
        start_snippet = seg_info["start_snippet"]
        end_snippet = seg_info["end_snippet"]

        # Snippet'leri metinde bul
        start_idx = chapter_text.find(start_snippet)

        if start_idx == -1:
            # Whitespace normalizasyonu ile tekrar dene
            normalized_text = " ".join(chapter_text.split())
            normalized_start = " ".join(start_snippet.split())
            start_idx = normalized_text.find(normalized_start)

            if start_idx == -1:
                print(f"    ⚠️  Start snippet bulunamadı: {start_snippet[:30]}...")
                continue

        # End snippet'i bul (rfind - en son eşleşme)
        end_idx = chapter_text.rfind(end_snippet, start_idx)

        if end_idx == -1:
            normalized_text = " ".join(chapter_text.split())
            normalized_end = " ".join(end_snippet.split())
            end_idx = normalized_text.rfind(normalized_end, start_idx)

            if end_idx == -1:
                print(f"    ⚠️  End snippet bulunamadı: {end_snippet[-30:]}")
                continue

        end_idx += len(end_snippet)

        # Segment metnini çıkar
        segment_text = chapter_text[start_idx:end_idx].strip()

        # Sayfa aralığını bul
        page_markers = re.findall(r"\[\[PAGE_(\d+)\]\]", segment_text)

        if page_markers:
            start_page = min(map(int, page_markers))
            end_page = max(map(int, page_markers))
        else:
            start_page = None
            end_page = None

        segments.append({
            "id": f"{chapter_id}_{local_id}",
            "chapter_id": chapter_id,
            "chapter_title": chapter_title,
            "segment_index": int(local_id),
            "text": segment_text,
            "start_page": start_page,
            "end_page": end_page,
            "source": os.path.basename(PDF_PATH)
        })

    return segments


def process_all_chapters(chapters: List[Dict]) -> List[Dict]:
    """
    Tüm chapter'ları işler ve segment'lere böler.

    Returns:
        List of all segments (JSONL ready)
    """
    print(f"\n✂️  Chapter'lar segmentlere bölünüyor...")

    all_segments = []

    for i, chapter in enumerate(chapters, 1):
        chapter_id = chapter["chapter_id"]
        chapter_title = chapter["chapter_title"]

        print(f"\n  [{i}/{len(chapters)}] {chapter_id} - {chapter_title[:50]}...")

        # LLM ile segmentasyon
        llm_segments = segment_chapter_with_llm(chapter)

        # Fallback: LLM başarısız olursa
        if not llm_segments:
            llm_segments = simple_segmentation_fallback(chapter["text"])

        # Gerçek segment'leri çıkar
        chapter_segments = extract_segments_from_text(chapter, llm_segments)

        if chapter_segments:
            all_segments.extend(chapter_segments)
            print(f"    ✓ {len(chapter_segments)} segment oluşturuldu")
        else:
            print(f"    ⚠️  Hiç segment çıkarılamadı!")

        # Rate limiting
        time.sleep(0.5)

    print(f"\n✓ Toplam {len(all_segments)} segment oluşturuldu")
    return all_segments


def write_jsonl(segments: List[Dict], output_path: str):
    """
    Segment'leri JSONL formatında yazar.
    """
    print(f"\n💾 JSONL yazılıyor: {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            f.write(json.dumps(segment, ensure_ascii=False) + "\n")

    print(f"✓ {len(segments)} segment yazıldı")

    # İstatistikler
    total_chars = sum(len(s["text"]) for s in segments)
    avg_chars = total_chars / len(segments) if segments else 0

    print(f"\n📊 İstatistikler:")
    print(f"   - Toplam segment: {len(segments)}")
    print(f"   - Ortalama uzunluk: {avg_chars:.0f} karakter")
    print(f"   - Min uzunluk: {min(len(s['text']) for s in segments):.0f} karakter")
    print(f"   - Max uzunluk: {max(len(s['text']) for s in segments):.0f} karakter")

    # Chapter dağılımı
    chapter_counts = {}
    for s in segments:
        ch = s["chapter_id"]
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

    print(f"   - Chapter sayısı: {len(chapter_counts)}")


def main():
    """Ana pipeline"""
    print("=" * 80)
    print("MAUG PDF CHUNKING PIPELINE")
    print("Chapter-aware, Table-safe Segmentation")
    print("=" * 80)

    if not os.path.exists(PDF_PATH):
        print(f"\n❌ HATA: PDF bulunamadı: {PDF_PATH}")
        print(f"   Lütfen PDF'i şu konuma koyun: {os.path.abspath(PDF_PATH)}")
        return

    start_time = time.time()

    # 1. PDF'ten metin çıkar (sayfa marker'ları ile)
    full_text = extract_text_with_page_markers(PDF_PATH)

    # 2. Chapter'ları tespit et (regex)
    chapters = detect_chapters(full_text)

    if not chapters:
        print("\n❌ Hiç chapter bulunamadı. İşlem sonlandırılıyor.")
        return

    # 3. Her chapter'ı segmentlere böl (LLM + deterministik)
    segments = process_all_chapters(chapters)

    if not segments:
        print("\n❌ Hiç segment oluşturulamadı. İşlem sonlandırılıyor.")
        return

    # 4. JSONL'e yaz
    write_jsonl(segments, OUTPUT_JSONL)

    elapsed = time.time() - start_time
    print(f"\n✅ İşlem tamamlandı! Süre: {elapsed:.2f} saniye")
    print(f"📄 Çıktı: {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
