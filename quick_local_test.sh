#!/bin/bash
# MAUG PDF Chunking - Linux/Mac Quick Test

set -e  # Exit on error

echo "================================"
echo "MAUG PDF Chunking - Quick Test"
echo "================================"

# 1. Sanal ortam oluştur
echo ""
echo "[1/6] Sanal ortam oluşturuluyor..."
python3 -m venv venv

# 2. Sanal ortamı aktive et
echo ""
echo "[2/6] Sanal ortam aktive ediliyor..."
source venv/bin/activate

# 3. Bağımlılıkları yükle
echo ""
echo "[3/6] Bağımlılıklar yükleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. .env kontrolü
echo ""
echo "[4/6] .env dosyası kontrol ediliyor..."
if [ ! -f .env ]; then
    echo ".env dosyası bulunamadı!"
    cp .env.example .env
    echo "UYARI: .env.example kopyalandı."
    echo "Lütfen .env dosyasını düzenleyip OPENAI_API_KEY ekleyin!"
    ${EDITOR:-nano} .env
fi

# 5. data/ klasörü ve PDF kontrolü
echo ""
echo "[5/6] PDF kontrol ediliyor..."
mkdir -p data

if [ ! -f data/MAUG_2_20221214_EBOOK.pdf ]; then
    if [ -f MAUG_2_20221214_EBOOK.pdf ]; then
        echo "PDF data/ klasörüne kopyalanıyor..."
        cp MAUG_2_20221214_EBOOK.pdf data/
    else
        echo "HATA: MAUG_2_20221214_EBOOK.pdf bulunamadı!"
        echo "Lütfen PDF'i şu konumlardan birine koyun:"
        echo "  - $(pwd)/data/MAUG_2_20221214_EBOOK.pdf"
        echo "  - $(pwd)/MAUG_2_20221214_EBOOK.pdf"
        exit 1
    fi
fi

# 6. Çalıştır
echo ""
echo "[6/6] MAUG chunking başlatılıyor..."
echo ""
echo "================================"
echo "İşlem başladı! (~5-10 dakika)"
echo "================================"
echo ""

python process_maug.py

echo ""
echo "================================"
echo "İşlem tamamlandı!"
echo "Çıktı: maug_chunks.jsonl"
echo "================================"
echo ""

# JSONL'i göster
if [ -f maug_chunks.jsonl ]; then
    echo "İlk 5 chunk:"
    head -n 5 maug_chunks.jsonl
    echo ""
    echo "Toplam chunk sayısı:"
    wc -l maug_chunks.jsonl
fi
