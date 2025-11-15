# VPS Deployment Kılavuzu - MAUG Chunking System

Bu kılavuz, yeni MAUG chunking dosyalarını VPS'ye güvenli bir şekilde kopyalamak için hazırlanmıştır.

## 🎯 Amaç

Mevcut VPS dosyalarını bozmadan sadece yeni MAUG chunking dosyalarını eklemek.

## 📦 Kopyalanacak Dosyalar

- ✅ `maug_chapters.json` - 57 chunk tanımı
- ✅ `index_maug_chapters.py` - Ana indexleme scripti
- ✅ `test_maug_chunks.py` - Test scripti
- ✅ `run_maug_test.sh` / `run_maug_index.sh` - Shell scriptleri
- ✅ `run_maug_test.bat` / `run_maug_index.bat` - Windows scriptleri
- ✅ `MAUG_CHUNKING_README.md` - Dokümantasyon

## 🚀 Deployment Yöntemleri

### Yöntem 1: Otomatik Deployment (Önerilen)

#### Linux/Mac:

1. **Script'i doğrudan çalıştırın (IP zaten ayarlanmış: 173.212.248.71):**
   ```bash
   chmod +x deploy_to_vps.sh
   ./deploy_to_vps.sh
   ```

#### Windows:

1. **Script'i doğrudan çalıştırın (IP zaten ayarlanmış: 173.212.248.71):**
   ```batch
   deploy_to_vps.bat
   ```

### Yöntem 2: Manuel Git Pull (VPS'de)

1. **VPS'ye SSH ile bağlanın:**
   ```bash
   ssh root@173.212.248.71
   ```

2. **Proje dizinine gidin:**
   ```bash
   cd /root/immunotherapy-api
   ```

3. **Update scriptini çalıştırın:**
   ```bash
   # Önce vps_update.sh'ı VPS'ye kopyalayın (sadece ilk seferinde)
   # Sonra:
   chmod +x vps_update.sh
   ./vps_update.sh
   ```

### Yöntem 3: Manuel Adım Adım (En Güvenli)

1. **VPS'ye SSH ile bağlanın:**
   ```bash
   ssh root@173.212.248.71
   ```

2. **Proje dizinine gidin:**
   ```bash
   cd /root/immunotherapy-api
   ```

3. **Mevcut değişiklikleri kaydedin (varsa):**
   ```bash
   git status
   # Eğer değişiklikler varsa:
   git stash
   ```

4. **Git repository'yi güncelleyin:**
   ```bash
   git fetch origin
   ```

5. **Yeni branch'e geçin:**
   ```bash
   git checkout claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
   git pull origin claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
   ```

6. **Yeni dosyaları kontrol edin:**
   ```bash
   ls -lh maug_chapters.json index_maug_chapters.py test_maug_chunks.py
   ```

## ✅ Deployment Sonrası Kontrol

VPS'de aşağıdaki adımları uygulayın:

### 1. Dosyaları Kontrol Edin

```bash
cd /root/immunotherapy-api

# Yeni dosyaların varlığını kontrol et
ls -lh maug_chapters.json
ls -lh index_maug_chapters.py
ls -lh test_maug_chunks.py
ls -lh run_maug_*.sh
ls -lh MAUG_CHUNKING_README.md
```

### 2. Test Çalıştırın

```bash
# Sanal ortamı aktif et
source venv/bin/activate

# Test scripti çalıştır (ilk 3 chunk)
python test_maug_chunks.py
```

**Beklenen çıktı:**
- ✓ JSON okundu: 57 chunk tanımı
- ✓ PDF açıldı: 576 sayfa
- İlk 3 chunk'ın içeriği gösterilir

### 3. Tam İndexleme (Opsiyonel)

```bash
# Tüm chunk'ları Qdrant'a yükle
./run_maug_index.sh

# VEYA
python index_maug_chapters.py
```

**Süre:** ~20-30 saniye (57 chunk × embedding)

### 4. Qdrant'ı Kontrol Edin

```bash
# Collection bilgisi
curl http://localhost:6333/collections/maug

# Veya Python ile
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='localhost', port=6333)
info = client.get_collection('maug')
print(f'Toplam chunk: {info.points_count}')
"
```

## 🔒 Güvenlik Kontrolleri

Deployment scriptleri şunları kontrol eder:

1. ✅ **Uncommitted changes:** Commit edilmemiş değişiklikler varsa uyarır
2. ✅ **SSH bağlantısı:** VPS'ye bağlantı test edilir
3. ✅ **Git stash:** Mevcut değişiklikler güvenli bir şekilde saklanır
4. ✅ **Branch kontrolü:** Doğru branch'e geçilir
5. ✅ **Sadece pull:** Mevcut dosyalar silinmez veya değiştirilmez

## ⚠️ Önemli Notlar

### Mevcut Dosyalar Etkilenmez

Aşağıdaki dosyalar **değiştirilmez**:

- ✅ `main.py` - FastAPI uygulaması
- ✅ `init_qdrant.py` - Mevcut Qdrant init
- ✅ `index_book.py` - Eski indexleme scripti
- ✅ `requirements.txt` - Python bağımlılıkları
- ✅ `.env` - Environment variables
- ✅ `data/book.pdf` - Mevcut PDF

Sadece **yeni MAUG dosyaları eklenir**.

### PDF Dosyası

`data/MAUG_2_20221214_EBOOK.pdf` dosyasını manuel olarak VPS'ye kopyalamanız gerekebilir:

```bash
# Local'den VPS'ye PDF kopyalama
scp data/MAUG_2_20221214_EBOOK.pdf root@173.212.248.71:/root/immunotherapy-api/data/
```

## 🆘 Sorun Giderme

### SSH Bağlantı Hatası

```bash
# SSH key kontrolü
ssh root@173.212.248.71

# Eğer çalışmıyorsa, şifre ile bağlanın
ssh -o PreferredAuthentications=password root@your-vps-ip
```

### Git Conflict

```bash
# VPS'de
cd /root/immunotherapy-api
git status

# Conflict varsa local değişiklikleri sil
git reset --hard origin/claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
```

### Dosyalar Görünmüyor

```bash
# Branch'i kontrol et
git branch --show-current

# Doğru branch'e geç
git checkout claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8

# Pull yap
git pull origin claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
```

## 📞 İletişim

Herhangi bir sorun yaşarsanız:

1. VPS loglarını kontrol edin
2. Git durumunu kontrol edin: `git status`
3. Manuel olarak dosyaları kopyalayın (Yöntem 3)
