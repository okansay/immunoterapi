#!/bin/bash
# MAUG chunk test scripti - İlk 3 chunk'ı gösterir

echo "=========================================="
echo "MAUG Chunk Test"
echo "=========================================="
echo ""

# Sanal ortamı aktif et
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "❌ venv bulunamadı! Lütfen önce 'python -m venv venv' çalıştırın."
    exit 1
fi

# Test scripti çalıştır
python test_maug_chunks.py

echo ""
echo "✅ Test tamamlandı!"
echo ""
echo "Tüm chunk'ları indexlemek için:"
echo "  ./run_maug_index.sh"
echo ""
