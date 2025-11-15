# MAUG PDF Indexleme - Hızlı Başlangıç

Bu kılavuz, MAUG (Molecular Allergology User's Guide) PDF'ini Qdrant'a yüklemeniz için gerekli adımları gösterir.

## 🎯 Özellikler

- ✅ **Predefined Chunks**: Her chapter için önceden belirlenmiş sayfa aralıkları
- ✅ **LLM'siz**: Chapter detection için LLM kullanılmaz (çok hızlı ve ucuz!)
- ✅ **PyMuPDF**: Daha iyi text extraction
- ✅ **Doğrudan Qdrant Upload**: JSONL ara dosyası yok

## 📋 Gereksinimler

1. Python 3.8+
2. Qdrant (Docker ile çalışıyor olmalı)
3. OpenAI API Key (sadece embedding için)
4. MAUG PDF dosyası

## 🚀 Kurulum Adımları

### 1. PDF Dosyasını Yerleştirin

```bash
# PDF'i data/ klasörüne koyun
cp /path/to/MAUG_2_20221214_EBOOK.pdf data/

# Kontrol edin
ls -lh data/MAUG_2_20221214_EBOOK.pdf
```

### 2. Environment Variables

`.env` dosyasını oluşturun (henüz yoksa):

```bash
cp .env.example .env
# OPENAI_API_KEY'i düzenleyin
nano .env
```

### 3. İndexleme İşlemini Başlatın

```bash
python3 index_maug_direct.py
```

## ⏱️ Süre ve Maliyet

- **Süre**: ~5-7 dakika (57 chunk)
- **Maliyet**: ~$0.02-0.03 (sadece embedding)
- **LLM Kullanımı**: YOK! (Sadece embedding API)

## 📊 Ne Yapılır?

1. PDF'den 57 chunk çıkarılır (predefined sayfa aralıkları)
2. Her chunk için OpenAI embedding oluşturulur
3. Qdrant'a yüklenir
4. Test aramaları yapılır

Detaylı kullanım için `MAUG_QUICKSTART.md` dosyasına bakın.
