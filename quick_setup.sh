#!/bin/bash
# MAUG Hızlı Kurulum Scripti

set -e  # Hata durumunda dur

echo "============================================"
echo "MAUG PDF → Qdrant Hızlı Kurulum"
echo "============================================"

# 1. .env kontrolü
echo ""
echo "1️⃣  .env dosyası kontrol ediliyor..."
if [ ! -f .env ]; then
    echo "   .env dosyası bulunamadı, oluşturuluyor..."
    cp .env.example .env
    echo "   ⚠️  .env dosyasını düzenleyin ve OPENAI_API_KEY ekleyin!"
    echo "   Sonra bu scripti tekrar çalıştırın."
    exit 1
fi

# API key kontrol
if grep -q "your_openai_api_key_here" .env; then
    echo "   ❌ OPENAI_API_KEY henüz eklenmemiş!"
    echo "   Lütfen .env dosyasını düzenleyin:"
    echo "   nano .env"
    exit 1
fi
echo "   ✅ .env dosyası hazır"

# 2. PDF kontrolü
echo ""
echo "2️⃣  PDF dosyası kontrol ediliyor..."
if [ ! -f data/MAUG_2_20221214_EBOOK.pdf ]; then
    echo "   ❌ PDF bulunamadı: data/MAUG_2_20221214_EBOOK.pdf"
    echo "   Lütfen PDF'i data/ klasörüne kopyalayın:"
    echo "   cp /path/to/MAUG_2_20221214_EBOOK.pdf data/"
    exit 1
fi
echo "   ✅ PDF hazır ($(ls -lh data/MAUG_2_20221214_EBOOK.pdf | awk '{print $5}'))"

# 3. Python paketleri
echo ""
echo "3️⃣  Python paketleri kontrol ediliyor..."
python3 -c "import fitz" 2>/dev/null || {
    echo "   PyMuPDF kurulu değil, kuruluyor..."
    pip install PyMuPDF==1.23.8
}
echo "   ✅ Python paketleri hazır"

# 4. Qdrant kontrolü
echo ""
echo "4️⃣  Qdrant kontrol ediliyor..."
if ! curl -s http://localhost:6333/collections >/dev/null 2>&1; then
    echo "   ⚠️  Qdrant çalışmıyor!"
    echo "   Docker ile başlatmak ister misiniz? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "   Qdrant başlatılıyor..."
        docker run -d -p 6333:6333 -p 6334:6334 \
          -v $(pwd)/qdrant_storage:/qdrant/storage:z \
          --name qdrant \
          qdrant/qdrant
        sleep 3
        echo "   ✅ Qdrant başlatıldı"
    else
        echo "   ❌ Qdrant olmadan devam edilemiyor"
        exit 1
    fi
else
    echo "   ✅ Qdrant çalışıyor"
fi

# 5. Collection oluştur
echo ""
echo "5️⃣  Qdrant collection oluşturuluyor..."
python3 init_qdrant.py
echo "   ✅ Collection hazır"

# 6. PDF'i indexle
echo ""
echo "6️⃣  PDF indexleniyor ve Qdrant'a yükleniyor..."
echo "   (Bu işlem ~5-7 dakika sürebilir)"
python3 index_maug_direct.py

# 7. Bitti
echo ""
echo "============================================"
echo "✅ Kurulum tamamlandı!"
echo "============================================"
echo ""
echo "API'yi başlatmak için:"
echo "  python3 main.py"
echo ""
echo "Test etmek için:"
echo "  curl http://localhost:8000/health"
echo ""
