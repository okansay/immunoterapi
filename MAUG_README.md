# MAUG PDF Chunking Pipeline

**Molecular Allergology User's Guide** PDF'ini chapter-aware, table-safe chunk'lara bölen deterministik + LLM pipeline.

---

## 🎯 Amaç

**Girdi**: `MAUG_2_20221214_EBOOK.pdf`

**Çıktı**: JSONL formatında chunk'lar

```json
{
  "id": "A01_01",
  "chapter_id": "A01",
  "chapter_title": "Molecular allergology coming of age...",
  "segment_index": 1,
  "text": "...",
  "start_page": 23,
  "end_page": 27,
  "source": "MAUG_2_20221214_EBOOK.pdf"
}
```

**Kullanım**: Embedding + vektör veritabanı (Pinecone, Qdrant, etc.)

---

## 🏗️ Mimari

### İki Katmanlı Yaklaşım

**1. Deterministik Katman**
- PDF → metin çıkarma (PyMuPDF)
- Sayfa marker ekleme: `[[PAGE_1]]`, `[[PAGE_2]]`, ...
- Chapter tespiti: Regex ile `A01 - Title`, `B02 - Title` pattern'ini yakala

**2. LLM Katmanı (GPT-4o-mini)**
- Her chapter → mantıklı segmentlere bölme
- Tablo/şekil koruması
- Alt başlıklarda kesim tercihi
- 500-1500 kelime hedefi

---

## 📋 Kurulum

### 1. PDF'i Yerleştirin

```bash
cp /path/to/MAUG_2_20221214_EBOOK.pdf data/
```

### 2. Bağımlılıkları Yükleyin

```bash
pip install PyMuPDF  # Henüz yüklemediyseniz
# veya
pip install -r requirements.txt
```

### 3. Environment Variables

`.env` dosyasında `OPENAI_API_KEY` ayarlı olmalı.

---

## 🚀 Kullanım

### Basit Kullanım

```bash
python process_maug.py
```

Çıktı: `maug_chunks.jsonl`

### Parametreleri Özelleştirme

`process_maug.py` dosyasının başındaki configuration bölümünü düzenleyin:

```python
# Configuration
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
OUTPUT_JSONL = "maug_chunks.jsonl"
LLM_MODEL = "gpt-4o-mini"

# Segmentation parameters
MIN_CHARS = 2000   # Minimum segment uzunluğu
MAX_CHARS = 8000   # Maximum segment uzunluğu
TARGET_WORDS = 800 # Hedef kelime sayısı
```

---

## 🔍 Nasıl Çalışır?

### Adım 1: PDF → Metin + Sayfa Marker

```python
[[PAGE_1]]
Preface from the EAACI president
...

[[PAGE_23]]
A01 - Molecular allergology coming of age...
...
```

### Adım 2: Chapter Tespiti (Regex)

**Pattern**: `^([ABCD]\d{2})\s*[–-]\s*(.+)$`

**Örnek eşleşmeler**:
- `A01 - Molecular allergology coming of age`
- `B14 – Allergy to mammalian meat`
- `C03 - Component-resolved diagnosis in food allergy`
- `D01 - Molecular allergology in clinical practice`

**Sonuç**:
```python
[
  {
    "chapter_id": "PREFACE",
    "chapter_title": "Prefaces and Introduction",
    "text": "..."
  },
  {
    "chapter_id": "A01",
    "chapter_title": "Molecular allergology coming of age...",
    "text": "A01 - Molecular...\n[[PAGE_23]]..."
  },
  ...
]
```

### Adım 3: LLM ile Segmentasyon

**Her chapter için GPT-4o-mini'ye gönderilir**:

**Sistem Promptu**:
- Metni değiştirme, sadece segment sınırlarını belirle
- Alt başlıklarda kes (subsection headings)
- Tablo/şekilleri bölme
- 500-1500 kelime hedefle

**Beklenen Çıktı** (JSON):
```json
{
  "segments": [
    {
      "local_id": "01",
      "start_snippet": "A01 - Molecular allergology coming...",
      "end_snippet": "...sensitising versus non-sensitising allergens."
    },
    {
      "local_id": "02",
      "start_snippet": "Sensitising versus non-sensitising...",
      "end_snippet": "...may differ between airborne and food allergens."
    }
  ]
}
```

### Adım 4: Snippet Matching + JSONL Yazma

- `start_snippet` ve `end_snippet` gerçek metinde bulunur
- Segment metni çıkarılır
- `[[PAGE_X]]` marker'larından sayfa aralığı hesaplanır
- JSONL'e yazılır

---

## 📊 Çıktı Formatı

### JSONL Örneği

```json
{"id": "A01_01", "chapter_id": "A01", "chapter_title": "Molecular allergology coming of age...", "segment_index": 1, "text": "A01 - Molecular allergology...", "start_page": 23, "end_page": 25, "source": "MAUG_2_20221214_EBOOK.pdf"}
{"id": "A01_02", "chapter_id": "A01", "chapter_title": "Molecular allergology coming of age...", "segment_index": 2, "text": "Sensitising versus non-sensitising...", "start_page": 26, "end_page": 27, "source": "MAUG_2_20221214_EBOOK.pdf"}
{"id": "B02_01", "chapter_id": "B02", "chapter_title": "Pollen allergen molecules...", "segment_index": 1, "text": "B02 - Pollen allergen molecules...", "start_page": 45, "end_page": 48, "source": "MAUG_2_20221214_EBOOK.pdf"}
```

### Alanlar

| Alan | Tip | Açıklama |
|------|-----|----------|
| `id` | string | Unique ID: `{chapter_id}_{segment_index}` |
| `chapter_id` | string | Chapter kodu: A01, B02, C11, etc. |
| `chapter_title` | string | Chapter başlığı |
| `segment_index` | int | Chapter içindeki segment sırası |
| `text` | string | Segment metni (sayfa marker'ları dahil) |
| `start_page` | int\|null | İlk sayfa numarası |
| `end_page` | int\|null | Son sayfa numarası |
| `source` | string | PDF dosya adı |

---

## 🛡️ Hata Yönetimi

### LLM JSON Hatası

**Problem**: GPT-4o-mini JSON formatında cevap vermedi

**Çözüm**:
1. JSON temizleme (markdown code block kaldırma)
2. Parse hatası varsa → Fallback: Basit paragraf bölme

### Snippet Bulunamadı

**Problem**: `start_snippet` veya `end_snippet` metinde yok

**Çözüm**:
1. Whitespace normalizasyonu (`\n` → boşluk, çoklu boşluk → tek)
2. Hâlâ yoksa → O segment atlanır, log'a yazılır

### Çok Kısa/Uzun Segmentler

**Problem**: Segment `MIN_CHARS` altında veya `MAX_CHARS` üstünde

**Çözüm**: Şu an sadece log'lanıyor, gelecekte merge/split eklenebilir

---

## 📈 Performans & Maliyet

### Örnek: 400 sayfalık PDF

- **Chapter sayısı**: ~50
- **LLM çağrısı**: 50 (her chapter için 1)
- **Token kullanımı**: ~50 × 4000 token ≈ 200K token
- **Maliyet**: ~$0.30-0.50 (GPT-4o-mini)
- **Süre**: ~5-10 dakika
- **Çıktı**: ~150-250 segment

---

## 🔧 Troubleshooting

### Problem: "PDF bulunamadı"

```bash
# PDF'in doğru yerde olduğunu kontrol edin
ls -l data/MAUG_2_20221214_EBOOK.pdf
```

### Problem: "Chapter bulunamadı"

- Chapter pattern'ini kontrol edin: `A01 - Title` formatında mı?
- PDF'ten metin düzgün çıkıyor mu?

### Problem: "Hiç segment oluşturulamadı"

- OpenAI API key geçerli mi?
- LLM response log'larını kontrol edin

---

## 🎯 Vektör Veritabanı Entegrasyonu

### Embedding Örneği

```python
import json
from openai import OpenAI

client = OpenAI()

# JSONL oku
chunks = []
with open("maug_chunks.jsonl", "r") as f:
    for line in f:
        chunks.append(json.loads(line))

# Her chunk için embedding
for chunk in chunks:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk["text"]
    )

    embedding = response.data[0].embedding

    # Qdrant/Pinecone'a kaydet
    # metadata: {
    #   id: chunk["id"],
    #   chapter_id: chunk["chapter_id"],
    #   chapter_title: chunk["chapter_title"],
    #   start_page: chunk["start_page"],
    #   end_page: chunk["end_page"],
    # }
```

### Metadata Filtreleme

```python
# Sadece A-series chapter'larda ara
filter = {"chapter_id": {"$like": "A%"}}

# Belirli sayfa aralığında ara
filter = {"start_page": {"$gte": 20, "$lte": 50}}
```

---

## 📝 Best Practices

1. **Önce küçük test**: İlk 5-10 chapter'la test edin
2. **LLM response'ları inceleyin**: Segmentasyon kalitesini kontrol edin
3. **Parametreleri ayarlayın**: `TARGET_WORDS` değerini use case'inize göre optimize edin
4. **Metadata kullanın**: Vektör aramada chapter/sayfa filtreleme yapın
5. **Backup alın**: JSONL çıktısını versiyon kontrolüne ekleyin

---

## 🚀 İleri Düzey

### Custom Chapter Pattern

Farklı bir PDF formatı için regex'i değiştirin:

```python
# Örnek: "Chapter 1:", "Chapter 2:" formatı
CHAPTER_PATTERN = re.compile(
    r"^Chapter\s+(\d+):\s*(.+)$",
    flags=re.MULTILINE
)
```

### Çoklu PDF İşleme

```python
pdf_files = ["maug1.pdf", "maug2.pdf"]

all_segments = []
for pdf in pdf_files:
    segments = process_pdf(pdf)
    all_segments.extend(segments)

write_jsonl(all_segments, "all_chunks.jsonl")
```

### Table Detection İyileştirme

`process_maug.py` içinde sistem promptuna ekleyin:

```python
system_prompt += """
Additional table detection rules:
- Lines with multiple consecutive tabs
- Rows with consistent column structure
- Lines starting with numbers followed by tabs
"""
```

---

## 📞 Destek

Sorular için: GitHub Issues veya proje README
