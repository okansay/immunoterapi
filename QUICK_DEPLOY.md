# 🚀 Hızlı Deployment - VPS'ye Kopyalama

## 1️⃣ En Hızlı Yöntem (Otomatik)

### Linux/Mac:
```bash
# IP zaten ayarlanmış: 173.212.248.71
# Doğrudan çalıştırın:
./deploy_to_vps.sh
```

### Windows:
```batch
REM IP zaten ayarlanmış: 173.212.248.71
REM Doğrudan çalıştırın:
deploy_to_vps.bat
```

---

## 2️⃣ Manuel Yöntem (En Güvenli)

### VPS'ye SSH ile Bağlan:
```bash
ssh root@173.212.248.71
cd /root/immunotherapy-api
```

### Tek Komutla Güncelle:
```bash
# Mevcut değişiklikleri kaydet (varsa)
git stash

# Yeni branch'i çek
git fetch origin
git checkout claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
git pull origin claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8

# Dosyaları kontrol et
ls -lh maug_chapters.json index_maug_chapters.py test_maug_chunks.py
```

### Test Et:
```bash
source venv/bin/activate
python test_maug_chunks.py
```

### Tam İndexleme (Opsiyonel):
```bash
./run_maug_index.sh
# VEYA
python index_maug_chapters.py
```

---

## ✅ Ne Kopyalanacak?

Sadece şu yeni dosyalar eklenir:
- ✅ maug_chapters.json (57 chunk tanımı)
- ✅ index_maug_chapters.py (indexleme scripti)
- ✅ test_maug_chunks.py (test scripti)
- ✅ run_maug_*.sh / *.bat (yardımcı scriptler)
- ✅ MAUG_CHUNKING_README.md (dokümantasyon)

**Mevcut dosyalarınız etkilenmez!**

---

## 📋 Deployment Sonrası Kontrol

```bash
# VPS'de
cd /root/immunotherapy-api

# Dosyaları kontrol et
ls -lh maug_chapters.json

# Test çalıştır
source venv/bin/activate
python test_maug_chunks.py

# Qdrant'ı kontrol et (indexleme yaptıysanız)
curl http://localhost:6333/collections/maug
```

Beklenen: 57 chunk Qdrant'ta

---

## 🆘 Sorun mu var?

### SSH bağlanamıyor:
```bash
ssh -v root@173.212.248.71  # Debug mode
```

### Dosyalar yok:
```bash
git branch --show-current  # Branch kontrolü
git pull origin claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
```

### PDF eksik:
```bash
# Local'den VPS'ye kopyala
scp data/MAUG_2_20221214_EBOOK.pdf root@173.212.248.71:/root/immunotherapy-api/data/
```

---

**Detaylı bilgi:** `VPS_DEPLOYMENT.md`
