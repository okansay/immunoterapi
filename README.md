# İmmünoterapi RAG Backend

İmmünoterapi konusunda karar destek veren RAG (Retrieval-Augmented Generation) tabanlı FastAPI backend'i.

## 🏗️ Sistem Mimarisi

```
Hostinger PHP Site → HTTP POST → Contabo VPS (FastAPI)
                                      ↓
                    Qdrant (Vector Search) + OpenAI (Embedding + LLM)
                                      ↓
                                  JSON Response
```

## 📋 Gereksinimler

- Python 3.8+
- Qdrant (Docker ile kurulu)
- OpenAI API Key

## 🚀 Kurulum

### 1. Sanal Ortam Oluşturma

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 2. Bağımlılıkları Yükleme

```bash
pip install -r requirements.txt
```

### 3. Environment Variables Ayarlama

`.env.example` dosyasını `.env` olarak kopyalayın ve doldurun:

```bash
cp .env.example .env
nano .env
```

`.env` içeriği:
```
OPENAI_API_KEY=sk-your-api-key-here
QDRANT_HOST=localhost
QDRANT_PORT=6333
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Qdrant'ı Başlatma (Docker)

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### 5. Qdrant Koleksiyonu Oluşturma

```bash
python init_qdrant.py
```

## 📚 PDF Kitabını İndexleme

### 1. PDF'i Yerleştirme

PDF kitabını `data/book.pdf` konumuna koyun:

```bash
mkdir -p data
cp /path/to/your/immunotherapy-book.pdf data/book.pdf
```

### 2. İndexleme İşlemini Başlatma

**ÖNERİLEN: Akıllı İndexleme (TOC tabanlı)**

```bash
python index_book_smart.py
```

Bu script:
- PDF bookmark/outline yapısını okur
- Bookmark yoksa → İlk 20 sayfadan **1 kez** LLM ile TOC çıkarır
- Sayfa → Chapter mapping oluşturur
- **Chapter sınırlarında chunk'ı keser**
- **Tablo/şekilleri bütün tutar**
- Embedding oluşturur (text-embedding-3-small)
- Qdrant'a kaydeder

⏱️ **Süre**: 576 sayfa için ~5-10 dakika
💰 **Maliyet**: ~$0.05-0.10 (sadece 1 LLM çağrısı)

**Alternatif: Her Chunk için LLM Analizi (eski yöntem)**

```bash
python index_book.py
```

⚠️ Daha yavaş (~45-60 dakika) ve daha maliyetli (~$3-5)
📖 Detaylı karşılaştırma için: `COMPARISON.md`

### 3. İndexleme Ayarları

Her iki script'te de parametreleri değiştirebilirsiniz:

```python
CHUNK_SIZE = 1000       # Her chunk'ın token boyutu
CHUNK_OVERLAP = 200     # Chunk'lar arası örtüşme
BATCH_SIZE = 10         # Qdrant'a aynı anda kaç chunk gönderilecek
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
```

## 🎯 API'yi Çalıştırma

```bash
python main.py
```

veya production için:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

API şu adreste çalışacak: `http://localhost:8000`

## 📡 API Endpoints

### 1. Health Check

```bash
GET /health
```

Yanıt:
```json
{
  "status": "healthy",
  "qdrant": "connected",
  "collection": "immunotherapy",
  "points_count": 1234,
  "vectors_count": 1234
}
```

### 2. Query (Soru Sorma)

```bash
POST /api/query
Content-Type: application/json

{
  "question": "Checkpoint inhibitörleri nasıl çalışır?",
  "language": "tr",
  "top_k": 5,
  "score_threshold": 0.7
}
```

Yanıt:
```json
{
  "answer": "Checkpoint inhibitörleri...",
  "sources": [
    {
      "chapter": "Checkpoint Inhibitors",
      "subsection": "Mechanism of Action",
      "page": "142-145",
      "relevance_score": 0.89
    }
  ],
  "processing_time": 2.341
}
```

### 3. cURL Örneği

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "CAR-T hücre tedavisi nedir?",
    "language": "tr"
  }'
```

## 🔍 Nasıl Çalışır?

### 1. İndexleme Süreci (Akıllı Yöntem)

```
PDF → TOC Extraction (1 LLM çağrısı veya Bookmark okuma)
          ↓
    Chapter Mapping Oluştur (Sayfa → Chapter)
          ↓
    Sayfa Çıkarma + Akıllı Chunking
          ↓
    - Chapter boundary'de kır
    - Tablo/şekil tespiti
    - Overlap uygula
          ↓
    Embedding (OpenAI)
          ↓
    Qdrant'a Kayıt
```

### 2. Sorgu Süreci

```
Kullanıcı Sorusu → Embedding → Vector Search (Qdrant)
                                      ↓
                              Top-K Benzer Chunk
                              (Chapter bilgisi ile)
                                      ↓
                      Context + Soru → GPT-4o-mini → Cevap
```

## 📊 Özellikler

✅ **TOC-based Chapter Detection**: PDF bookmark veya 1 kez LLM ile TOC çıkarımı
✅ **Chapter Boundary Awareness**: Chapter ortasında chunk kesme yok
✅ **Table/Figure Protection**: Tablo ve şekiller bütün kalır
✅ **Overlap Chunking**: Bilgi kaybını önlemek için chunk'lar arası örtüşme
✅ **Semantic Search**: Vektör benzerliğine dayalı arama
✅ **Multi-language**: Türkçe ve İngilizce destek
✅ **Source Tracking**: Her cevap kaynak bilgileriyle gelir
✅ **Fast & Scalable**: Qdrant ile hızlı arama
✅ **Cost Efficient**: %95 daha düşük indexleme maliyeti

## 🛠️ Troubleshooting

### Problem: "Collection not found"

```bash
python init_qdrant.py
```

### Problem: "PDF not found"

PDF'in doğru konumda olduğundan emin olun:
```bash
ls -l data/book.pdf
```

### Problem: "OpenAI API Error"

`.env` dosyasında API key'in doğru olduğunu kontrol edin:
```bash
cat .env | grep OPENAI_API_KEY
```

### Problem: "httpx version conflict"

```bash
pip install httpx==0.27.0 --force-reinstall
```

## 📝 Geliştirme Notları

- **Embedding Model**: `text-embedding-3-small` (1536 boyut)
- **LLM Model**: `gpt-4o-mini` (TOC extraction ve response generation için)
- **Vector Distance**: Cosine similarity
- **Chunk Strategy**: Chapter-aware, table-safe, paragraph-based with token limit
- **Rate Limiting**: OpenAI API için 0.3 saniye bekleme
- **TOC Extraction**: PDF bookmarks → LLM fallback → Page-based grouping
- **Table Detection**: Pattern matching + structural analysis

## 🔐 Güvenlik

Production'da:
- CORS ayarlarını domain ile sınırlandırın
- API rate limiting ekleyin (SlowAPI)
- HTTPS kullanın
- API key'leri güvenli tutun

## 📞 Destek

Sorunlar için: GitHub Issues
