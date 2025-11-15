#!/bin/bash
# VPS'ye güvenli deployment scripti
# Mevcut dosyaları bozmadan sadece yeni MAUG dosyalarını ekler

set -e  # Hata durumunda dur

echo "=========================================="
echo "VPS Deployment - MAUG Chunking System"
echo "=========================================="
echo ""

# Konfigürasyon
VPS_USER="root"
VPS_HOST="173.212.248.71"
VPS_PROJECT_DIR="/root/immunotherapy-api"
BRANCH_NAME="claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8"

# VPS bilgilerini kontrol et
if [ "$VPS_HOST" = "your-vps-ip-or-hostname" ]; then
    echo "❌ HATA: Lütfen VPS_HOST değişkenini düzenleyin!"
    echo "   Script içinde VPS_HOST='your-vps-ip-or-hostname' satırını"
    echo "   gerçek VPS IP adresi veya hostname ile değiştirin."
    echo ""
    echo "Örnek:"
    echo "   VPS_HOST='185.123.45.67'"
    echo "   VPS_HOST='immunotherapy.example.com'"
    exit 1
fi

echo "📋 Deployment Bilgileri:"
echo "   VPS: $VPS_USER@$VPS_HOST"
echo "   Dizin: $VPS_PROJECT_DIR"
echo "   Branch: $BRANCH_NAME"
echo ""

# SSH bağlantısını test et
echo "🔍 VPS bağlantısı test ediliyor..."
if ! ssh -o ConnectTimeout=5 "$VPS_USER@$VPS_HOST" "echo 'Bağlantı başarılı'" 2>/dev/null; then
    echo "❌ VPS'ye SSH bağlantısı kurulamadı!"
    echo ""
    echo "Çözümler:"
    echo "  1. VPS IP adresini kontrol edin"
    echo "  2. SSH key'inizin kurulu olduğundan emin olun"
    echo "  3. Manuel bağlantı deneyin: ssh $VPS_USER@$VPS_HOST"
    exit 1
fi

echo "✓ VPS bağlantısı başarılı"
echo ""

# Git durumunu kontrol et
echo "🔍 Git durumu kontrol ediliyor..."
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ UYARI: Commit edilmemiş değişiklikler var!"
    echo ""
    git status --short
    echo ""
    read -p "Devam etmek istiyor musunuz? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "✓ Git durumu temiz"
echo ""

# VPS'de deployment yap
echo "🚀 VPS'de deployment başlıyor..."
echo ""

ssh "$VPS_USER@$VPS_HOST" bash << 'ENDSSH'
set -e

echo "📂 Proje dizinine geçiliyor..."
cd /root/immunotherapy-api

echo "📊 Mevcut durum:"
git branch --show-current
git status --short

echo ""
echo "🔄 Git fetch yapılıyor..."
git fetch origin

echo ""
echo "🔀 Branch değiştiriliyor ve pull yapılıyor..."
# Eğer branch yoksa oluştur
if ! git show-ref --verify --quiet refs/heads/claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8; then
    echo "   → Branch local'de yok, oluşturuluyor..."
    git checkout -b claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8 origin/claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
else
    echo "   → Branch mevcut, checkout yapılıyor..."
    git checkout claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
    git pull origin claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8
fi

echo ""
echo "📋 Yeni dosyalar:"
ls -lh maug_chapters.json index_maug_chapters.py test_maug_chunks.py 2>/dev/null || echo "   (dosyalar henüz görünmüyor)"

echo ""
echo "✓ VPS deployment tamamlandı!"

ENDSSH

echo ""
echo "=========================================="
echo "✅ Deployment başarıyla tamamlandı!"
echo "=========================================="
echo ""
echo "📝 Sonraki adımlar (VPS'de):"
echo ""
echo "1. VPS'ye bağlanın:"
echo "   ssh $VPS_USER@$VPS_HOST"
echo ""
echo "2. Proje dizinine gidin:"
echo "   cd $VPS_PROJECT_DIR"
echo ""
echo "3. Test çalıştırın:"
echo "   source venv/bin/activate"
echo "   python test_maug_chunks.py"
echo ""
echo "4. Tam indexleme yapın:"
echo "   ./run_maug_index.sh"
echo ""
