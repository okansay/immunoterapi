# MAUG Chunking - Quick Start

5 dakikada MAUG PDF'ini chunk'lara bölün!

---

## ⚡ Hızlı Başlangıç

### 1. PDF'i Hazırlayın

```bash
# PDF'i data/ klasörüne kopyalayın
cp /path/to/MAUG_2_20221214_EBOOK.pdf data/
```

### 2. Bağımlılıkları Yükleyin

```bash
# PyMuPDF'i yükleyin
pip install PyMuPDF==1.23.8

# veya tüm bağımlılıkları
pip install -r requirements.txt
```

### 3. Çalıştırın

```bash
python process_maug.py
```

**Beklenen süre**: ~5-10 dakika (PDF boyutuna göre)

**Çıktı**: `maug_chunks.jsonl`

---

## 📄 Çıktı Örneği

```json
{"id": "A01_01", "chapter_id": "A01", "chapter_title": "Molecular allergology...", "segment_index": 1, "text": "...", "start_page": 23, "end_page": 25, "source": "MAUG_2_20221214_EBOOK.pdf"}
{"id": "A01_02", "chapter_id": "A01", "chapter_title": "Molecular allergology...", "segment_index": 2, "text": "...", "start_page": 26, "end_page": 27, "source": "MAUG_2_20221214_EBOOK.pdf"}
```

---

## 🔍 Çıktıyı İnceleme

```bash
# İlk 5 chunk'ı görün
head -n 5 maug_chunks.jsonl

# Toplam chunk sayısı
wc -l maug_chunks.jsonl

# Belirli chapter'a ait chunk'lar
grep '"chapter_id": "A01"' maug_chunks.jsonl
```

---

## 📊 İstatistikler

Script otomatik olarak istatistik yazdırır:

```
✓ Toplam 187 segment oluşturuldu

📊 İstatistikler:
   - Toplam segment: 187
   - Ortalama uzunluk: 3245 karakter
   - Min uzunluk: 1823 karakter
   - Max uzunluk: 7891 karakter
   - Chapter sayısı: 52
```

---

## 🎯 Embedding'e Gönderme

### Qdrant Örneği

```python
import json
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

client = OpenAI()
qdrant = QdrantClient(host="localhost", port=6333)

# JSONL oku
chunks = []
with open("maug_chunks.jsonl", "r") as f:
    for line in f:
        chunks.append(json.loads(line))

# Her chunk için embedding + upload
for chunk in chunks:
    # Embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk["text"]
    )
    embedding = response.data[0].embedding

    # Qdrant'a kaydet
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "id": chunk["id"],
            "chapter_id": chunk["chapter_id"],
            "chapter_title": chunk["chapter_title"],
            "text": chunk["text"],
            "start_page": chunk["start_page"],
            "end_page": chunk["end_page"],
            "source": chunk["source"]
        }
    )

    qdrant.upsert(
        collection_name="maug",
        points=[point]
    )

print(f"✓ {len(chunks)} chunk Qdrant'a yüklendi")
```

---

## 🛠️ Sorun Giderme

### "PDF bulunamadı"

```bash
# PDF'in doğru yerde olduğunu kontrol edin
ls -l data/MAUG_2_20221214_EBOOK.pdf
```

### "Chapter bulunamadı"

PDF'in chapter pattern'i farklıysa `process_maug.py` içindeki regex'i değiştirin:

```python
CHAPTER_PATTERN = re.compile(
    r"^([ABCD]\d{2})\s*[–-]\s*(.+)$",  # Mevcut pattern
    flags=re.MULTILINE
)
```

### "OpenAI API Error"

```bash
# .env dosyasında API key'i kontrol edin
cat .env | grep OPENAI_API_KEY
```

---

## 📝 İleri Adımlar

1. **Detaylı Dokümantasyon**: `MAUG_README.md`
2. **Parametreleri Özelleştirme**: `maug_config.example.py`
3. **Vektör DB Entegrasyonu**: Qdrant/Pinecone setup

---

## ✅ Checklist

- [ ] PDF'i `data/` klasörüne kopyaladım
- [ ] PyMuPDF kurdum
- [ ] `.env` dosyasında `OPENAI_API_KEY` var
- [ ] `python process_maug.py` çalıştırdım
- [ ] `maug_chunks.jsonl` oluştu
- [ ] Chunk'ları inceledim
- [ ] Embedding'e göndermeye hazırım

---

Başarılar! 🚀
