# MAUG PDF Chunking - JSON Tabanlı Deterministik Sistem

JSON tanımına göre MAUG PDF'ini chapter'lara bölen ve Qdrant'a yükleyen sistem.

## Dosyalar

### Ana Dosyalar
- `maug_chapters.json` - 57 chunk tanımı (sayfa aralıkları ile)
- `index_maug_chapters.py` - Ana script (chunk'ları çıkarır, embedding yapar, Qdrant'a yükler)
- `test_maug_chunks.py` - Test scripti (ilk 3 chunk'ı gösterir)

### Gerekli PDF
- `data/MAUG_2_20221214_EBOOK.pdf` - Ana PDF dosyası (576 sayfa)

## Kullanım

### 1. Test (İlk 3 chunk'ı görüntüle)

```bash
# Sanal ortamı aktif et
source venv/bin/activate

# Test yap
python test_maug_chunks.py
```

Bu komut:
- İlk 3 chunk'ı PDF'den çıkarır
- Kelime/karakter sayılarını gösterir
- İçeriğin başını ve sonunu gösterir
- **Embedding yapmaz, Qdrant'a yüklemez**

### 2. Tam İndexleme (Tüm chunk'lar)

```bash
# Sanal ortamı aktif et
source venv/bin/activate

# Tam indexleme
python index_maug_chapters.py
```

Bu komut:
1. 57 chunk tanımını `maug_chapters.json`'dan okur
2. Her chunk için PDF'den belirtilen sayfaları çıkarır
3. Her chunk için OpenAI embedding oluşturur (`text-embedding-3-small`)
4. Tüm chunk'ları Qdrant'a yükler (`maug` collection)
5. Test araması yapar

**Süre:** ~3-5 dakika (OpenAI API rate limiting nedeniyle)

### 3. Sonuçları Kontrol Et

```bash
# Qdrant'ta chunk sayısını gör
curl http://localhost:6333/collections/maug
```

Veya Python ile:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collection_info = client.get_collection("maug")
print(f"Toplam chunk: {collection_info.points_count}")
```

## JSON Chunk Yapısı

Her chunk şu bilgileri içerir:

```json
{
  "chunk_id": "A01",
  "section": "A",
  "code": "A01",
  "title": "Molecular allergology coming of age...",
  "start_page": 19,
  "end_page": 22
}
```

## Qdrant'ta Saklanan Metadata

Her chunk Qdrant'ta şu payload ile saklanır:

```json
{
  "chunk_id": "A01",
  "section": "A",
  "code": "A01",
  "title": "...",
  "start_page": 19,
  "end_page": 22,
  "page": "19-22",
  "text": "...",
  "source": "MAUG_2_20221214_EBOOK.pdf",
  "char_count": 12345,
  "word_count": 1234
}
```

## Özellikler

✅ **Deterministik:** GPT kullanılmaz, sayfa aralıklarına göre kesin bölme
✅ **Chapter-aware:** Her chunk bir chapter/section'a ait
✅ **Metadata-rich:** Section, code, title, page bilgileri
✅ **Test-friendly:** Önce test scriptini çalıştırıp sonuçları görebilirsiniz
✅ **Batch upload:** Qdrant'a 10'lu gruplar halinde yükleme (rate limiting)

## Bölümler (Sections)

- **FRONT** - Ön kapak, içindekiler (1-14)
- **PREFACE** - Önsözler (15-18)
- **A** - Metodoloji ve genel bilgiler (A01-A12, sayfa 19-170)
- **B** - Allerjen kaynakları (B01-B22, sayfa 171-452)
- **C** - Protein aileleri (C01-C11, sayfa 453-564)
- **D** - Referans tablosu (D01, sayfa 565-576)

Toplam: **57 chunk**

## Sorun Giderme

### PDF bulunamadı
```bash
# PDF'in doğru yerde olduğunu kontrol et
ls -lh data/MAUG_2_20221214_EBOOK.pdf
```

### Qdrant bağlantı hatası
```bash
# Qdrant'ın çalıştığını kontrol et
curl http://localhost:6333/collections
```

### OpenAI API hatası
```bash
# .env dosyasında API key olduğunu kontrol et
grep OPENAI_API_KEY .env
```

## Performans

- **57 chunk** × 0.3 saniye rate limit = ~17 saniye (embedding)
- OpenAI API gecikmeleri: +5-10 saniye
- Toplam süre: **~20-30 saniye**

## Diğer Notlar

- Eski `process_maug.py` - LLM ile dinamik segmentasyon (kullanılmıyor)
- Eski `upload_maug_to_qdrant.py` - JSONL'den yükleme (kullanılmıyor)
- Yeni sistem daha basit, daha hızlı, daha öngörülebilir
