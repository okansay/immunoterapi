#!/usr/bin/env python3
"""
MAUG chunk'larının doğru çıkarıldığını test eder.
İlk 3 chunk'ı gösterir (embedding yapmaz, Qdrant'a yüklemez).
"""

import os
import json
import fitz  # PyMuPDF

# Configuration
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
CHUNKS_JSON = "maug_chapters.json"
MAX_CHUNKS_TO_TEST = 3


def load_chunk_definitions(json_path: str):
    """JSON dosyasından chunk tanımlarını okur."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chunks", [])


def extract_chunk_from_pdf(pdf_doc: fitz.Document, chunk_def: dict) -> str:
    """PDF'den chunk metnini çıkarır."""
    start_page = chunk_def["start_page"]
    end_page = chunk_def["end_page"]

    pages_text = []
    for page_num in range(start_page - 1, end_page):  # 0-indexed
        if page_num >= len(pdf_doc):
            break
        page = pdf_doc[page_num]
        page_text = page.get_text("text")
        pages_text.append(page_text)

    return "\n\n".join(pages_text).strip()


def main():
    """Ana test fonksiyonu"""
    print("=" * 80)
    print("MAUG CHUNK TEST")
    print("İlk birkaç chunk'ı çıkarıp gösterir")
    print("=" * 80)

    # Dosya kontrolleri
    if not os.path.exists(PDF_PATH):
        print(f"\n❌ PDF bulunamadı: {PDF_PATH}")
        return

    if not os.path.exists(CHUNKS_JSON):
        print(f"\n❌ JSON bulunamadı: {CHUNKS_JSON}")
        return

    # JSON'u oku
    print(f"\n📖 JSON okunuyor: {CHUNKS_JSON}")
    chunk_definitions = load_chunk_definitions(CHUNKS_JSON)
    print(f"✓ {len(chunk_definitions)} chunk tanımı bulundu")

    # PDF'i aç
    print(f"\n📖 PDF açılıyor: {PDF_PATH}")
    pdf_doc = fitz.open(PDF_PATH)
    print(f"✓ PDF açıldı - Toplam {len(pdf_doc)} sayfa")

    # İlk birkaç chunk'ı test et
    print(f"\n🧪 İlk {MAX_CHUNKS_TO_TEST} chunk test ediliyor...")
    print("=" * 80)

    for i, chunk_def in enumerate(chunk_definitions[:MAX_CHUNKS_TO_TEST], 1):
        chunk_id = chunk_def["chunk_id"]
        title = chunk_def["title"]
        start_page = chunk_def["start_page"]
        end_page = chunk_def["end_page"]

        print(f"\n[{i}/{MAX_CHUNKS_TO_TEST}] Chunk ID: {chunk_id}")
        print(f"Title: {title}")
        print(f"Pages: {start_page}-{end_page}")

        # Metni çıkar
        chunk_text = extract_chunk_from_pdf(pdf_doc, chunk_def)

        if not chunk_text.strip():
            print("⚠️  UYARI: Boş chunk!")
            continue

        word_count = len(chunk_text.split())
        char_count = len(chunk_text)

        print(f"Word count: {word_count}")
        print(f"Char count: {char_count}")
        print(f"\n--- İlk 300 karakter ---")
        print(chunk_text[:300])
        print(f"\n--- Son 200 karakter ---")
        print(chunk_text[-200:])
        print("=" * 80)

    pdf_doc.close()

    print(f"\n✅ Test tamamlandı!")
    print(f"📄 Tüm chunk'ları işlemek için: python index_maug_chapters.py")


if __name__ == "__main__":
    main()
