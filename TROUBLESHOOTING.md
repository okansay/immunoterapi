# Sorun Giderme Kılavuzu

## 🔴 Script Kilitleniyor / Donuyor

### 1️⃣ Hangi Aşamada Kilitlenir?

**Test etmek için debug versiyonu çalıştırın:**

```bash
python3 index_maug_direct_debug.py
```

Bu versiyon her adımı ekrana yazdırır ve nerelerde takıldığını gösterir.

---

### 2️⃣ Yaygın Kilitleme Nedenleri

#### A. OpenAI API Timeout

**Belirtiler:**
- "Embedding oluşturuluyor..." yazısında takılır
- Uzun süre yanıt gelmez

**Çözüm:**

```python
# index_maug_direct.py içinde timeout ekleyin
response = client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=chunk["text"],
    timeout=30.0  # 30 saniye timeout
)
```

**Veya:**

```bash
# Network timeout ayarı (VPS'te)
export OPENAI_API_TIMEOUT=60
python3 index_maug_direct.py
```

---

#### B. Qdrant Bağlantı Sorunu

**Test:**

```bash
# Qdrant'a erişim var mı?
curl http://localhost:6333/collections

# Yanıt yoksa Qdrant çalışmıyor
docker ps | grep qdrant

# Başlat
docker start qdrant
# veya
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

---

#### C. Memory Yetersizliği

**Belirtiler:**
- "Killed" mesajı
- Script aniden kapanır
- VPS donması

**Çözüm 1: Küçük batch size**

```python
# index_maug_direct.py içinde
BATCH_SIZE = 3  # 10'dan küçült
```

**Çözüm 2: Swap alanı ekle (VPS'te)**

```bash
# Swap kontrolü
free -h

# Swap ekle (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

#### D. SSH Bağlantısı Kopuyor

**Çözüm: Screen veya tmux kullanın**

```bash
# Screen başlat
screen -S maug_upload

# İçinde scripti çalıştır
python3 index_maug_direct.py

# Detach (bağlantı kopsa bile devam eder): Ctrl+A, D

# Geri dön
screen -r maug_upload

# Screen listesi
screen -ls
```

**Veya tmux:**

```bash
tmux new -s maug_upload
python3 index_maug_direct.py
# Detach: Ctrl+B, D
# Geri dön: tmux attach -t maug_upload
```

---

### 3️⃣ Minimal Test (İlk 10 Chunk)

Tam upload öncesi küçük bir test yapın:

```bash
# Sadece 10 chunk yükler (hızlı test)
python3 index_maug_minimal.py
```

Bu başarılı olursa tam upload yapın:

```bash
python3 index_maug_direct.py
```

---

## 🔴 OpenAI API Hataları

### Rate Limit Hatası

**Hata:**
```
RateLimitError: Rate limit exceeded
```

**Çözüm:**

```python
# index_maug_direct.py içinde bekleme süresini artırın
time.sleep(1.0)  # 0.3'ten 1.0'a çıkar
```

**Veya:**

```bash
# Daha yavaş upload
python3 index_maug_direct.py 2>&1 | tee upload.log
```

---

### API Key Hatası

**Hata:**
```
AuthenticationError: Invalid API key
```

**Çözüm:**

```bash
# .env kontrolü
cat .env | grep OPENAI_API_KEY

# Doğru formatta mı?
# OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxx

# Test et
python3 -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); c = OpenAI(); print(c.models.list().data[0].id)"
```

---

### Timeout Hatası

**Hata:**
```
Timeout: Request timed out
```

**Çözüm:**

```bash
# Retry mekanizması ekle
pip install tenacity

# Veya timeout artır
export OPENAI_API_TIMEOUT=120
```

---

## 🔴 Qdrant Hataları

### Collection Bulunamadı

**Hata:**
```
Collection not found: immunotherapy
```

**Çözüm:**

```bash
python3 init_qdrant.py
```

---

### Qdrant Connection Refused

**Hata:**
```
Connection refused on localhost:6333
```

**Çözüm:**

```bash
# Qdrant durumunu kontrol et
docker ps -a | grep qdrant

# Çalışmıyorsa başlat
docker start qdrant

# Hiç yoksa oluştur
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  --name qdrant \
  qdrant/qdrant

# 2-3 saniye bekle
sleep 3

# Test et
curl http://localhost:6333/collections
```

---

## 🔴 PDF Hataları

### PDF Bulunamadı

**Hata:**
```
FileNotFoundError: data/MAUG_2_20221214_EBOOK.pdf
```

**Çözüm:**

```bash
# PDF var mı?
ls -lh data/MAUG_2_20221214_EBOOK.pdf

# Yoksa kopyala
cp /path/to/MAUG.pdf data/MAUG_2_20221214_EBOOK.pdf
```

---

### PyMuPDF Hatası

**Hata:**
```
ModuleNotFoundError: No module named 'fitz'
```

**Çözüm:**

```bash
pip install PyMuPDF==1.23.8

# Kontrol
python3 -c "import fitz; print(fitz.__version__)"
```

---

## 🔴 VPS Performans Sorunları

### CPU %100

```bash
# CPU kullanımını kontrol et
top

# Python işlemini görürseniz normal (embedding hesaplama)
# Beklemeniz gerekiyor
```

---

### Disk Dolu

```bash
# Disk kullanımını kontrol et
df -h

# Qdrant storage temizle (DİKKAT: tüm vektörleri siler)
rm -rf qdrant_storage/*
```

---

### RAM Yetersiz

```bash
# RAM kontrolü
free -h

# Swap ekle (yukarıda anlatıldı)
# Veya daha küçük batch size kullan
```

---

## ✅ Önerilen Çalışma Akışı

```bash
# 1. Bağlantı kopmayacak şekilde başlat
screen -S maug_upload

# 2. Debug mode ile test
python3 index_maug_direct_debug.py

# 3. Sorun yoksa minimal test
python3 index_maug_minimal.py

# 4. Her şey çalışıyorsa tam upload
python3 index_maug_direct.py 2>&1 | tee upload.log

# 5. Detach (güvenli çıkış)
# Ctrl+A, D

# 6. Daha sonra geri dön
screen -r maug_upload
```

---

## 📊 Log Dosyası İnceleme

Eğer kilitlendiyse log dosyasını inceleyin:

```bash
# Log dosyası varsa
tail -f upload.log

# Son hataları görün
grep -i error upload.log
grep -i timeout upload.log
```

---

## 🆘 Acil Durum: Manuel Upload

Script hiç çalışmıyorsa manuel olarak:

```python
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid
import fitz

# Clients
client = OpenAI(api_key="YOUR_KEY")
qdrant = QdrantClient("localhost", 6333)

# PDF
doc = fitz.open("data/MAUG_2_20221214_EBOOK.pdf")
text = doc[18].get_text()  # Sadece sayfa 19 (A01 başlangıcı)

# Embedding
emb = client.embeddings.create(model="text-embedding-3-small", input=text)

# Upload
qdrant.upsert(
    collection_name="immunotherapy",
    points=[PointStruct(
        id=str(uuid.uuid4()),
        vector=emb.data[0].embedding,
        payload={"text": text, "page": 19}
    )]
)

print("✓ Test chunk yüklendi!")
```

---

## 📞 Daha Fazla Yardım

Sorununuz devam ediyorsa:

1. Hangi script'i çalıştırdığınız
2. Hangi aşamada takıldığı
3. Hata mesajı (varsa)
4. VPS özellikleri (RAM, CPU)

Bu bilgilerle daha spesifik yardım edebilirim.
