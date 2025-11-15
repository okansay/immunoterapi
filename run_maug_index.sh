#!/bin/bash
# MAUG full indexing - Tüm chunk'ları Qdrant'a yükler

echo "=========================================="
echo "MAUG Full Indexing"
echo "=========================================="
echo ""
echo "⚠️  Bu işlem:"
echo "   - 57 chunk oluşturacak"
echo "   - OpenAI API kullanacak (embedding)"
echo "   - Qdrant'a yükleyecek"
echo "   - ~20-30 saniye sürecek"
echo ""
read -p "Devam etmek istiyor musunuz? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "İşlem iptal edildi."
    exit 0
fi

# Sanal ortamı aktif et
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "❌ venv bulunamadı!"
    exit 1
fi

# Qdrant kontrolü
echo ""
echo "🔍 Qdrant bağlantısı kontrol ediliyor..."
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✓ Qdrant çalışıyor"
else
    echo "❌ Qdrant'a bağlanılamadı!"
    echo "   Lütfen Qdrant'ı başlatın: docker-compose up -d"
    exit 1
fi

# Ana script çalıştır
echo ""
python index_maug_chapters.py

echo ""
echo "=========================================="
echo "✅ İşlem tamamlandı!"
echo "=========================================="
echo ""
echo "Qdrant collection bilgisi:"
curl -s http://localhost:6333/collections/maug | python -m json.tool
echo ""
