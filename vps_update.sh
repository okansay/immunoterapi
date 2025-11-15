#!/bin/bash
# VPS üzerinde çalıştırılacak update scripti
# Bu script'i VPS'de /root/immunotherapy-api dizininde çalıştırın

set -e

echo "=========================================="
echo "VPS Update - MAUG Chunking System"
echo "=========================================="
echo ""

# Proje dizinini kontrol et
if [ ! -d ".git" ]; then
    echo "❌ HATA: Bu dizin bir git repository değil!"
    echo "   Lütfen /root/immunotherapy-api dizininde çalıştırın"
    exit 1
fi

echo "📂 Mevcut dizin: $(pwd)"
echo "📊 Mevcut branch: $(git branch --show-current)"
echo ""

# Uncommitted changes kontrolü
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  UYARI: Commit edilmemiş değişiklikler var!"
    echo ""
    git status --short
    echo ""
    echo "Bu değişiklikler stash'lenecek..."
    git stash push -m "Auto-stash before MAUG update $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✓ Değişiklikler stash'lendi (git stash pop ile geri alabilirsiniz)"
    echo ""
fi

# Git fetch
echo "🔄 Git repository güncelleniyor..."
git fetch origin

# Branch değiştir/güncelle
BRANCH_NAME="claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8"

echo ""
echo "🔀 Branch: $BRANCH_NAME"

if ! git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
    echo "   → Branch local'de yok, oluşturuluyor..."
    git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
else
    echo "   → Branch mevcut, checkout ve pull yapılıyor..."
    git checkout $BRANCH_NAME
    git pull origin $BRANCH_NAME
fi

echo ""
echo "✓ Git güncelleme tamamlandı"
echo ""

# Yeni dosyaları göster
echo "📋 Yeni MAUG dosyaları:"
echo ""
ls -lh maug_chapters.json 2>/dev/null && echo "   ✓ maug_chapters.json" || echo "   ✗ maug_chapters.json eksik"
ls -lh index_maug_chapters.py 2>/dev/null && echo "   ✓ index_maug_chapters.py" || echo "   ✗ index_maug_chapters.py eksik"
ls -lh test_maug_chunks.py 2>/dev/null && echo "   ✓ test_maug_chunks.py" || echo "   ✗ test_maug_chunks.py eksik"
ls -lh run_maug_*.sh 2>/dev/null && echo "   ✓ Shell scripts" || echo "   ✗ Shell scripts eksik"
ls -lh MAUG_CHUNKING_README.md 2>/dev/null && echo "   ✓ README" || echo "   ✗ README eksik"

echo ""
echo "=========================================="
echo "✅ Update tamamlandı!"
echo "=========================================="
echo ""
echo "📝 Sonraki adımlar:"
echo ""
echo "1. Sanal ortamı aktif edin:"
echo "   source venv/bin/activate"
echo ""
echo "2. Test çalıştırın:"
echo "   python test_maug_chunks.py"
echo ""
echo "3. Tam indexleme yapın:"
echo "   ./run_maug_index.sh"
echo ""
echo "4. README'yi okuyun:"
echo "   cat MAUG_CHUNKING_README.md"
echo ""
