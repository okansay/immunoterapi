@echo off
REM VPS'ye güvenli deployment scripti (Windows)
REM Mevcut dosyaları bozmadan sadece yeni MAUG dosyalarını ekler

setlocal enabledelayedexpansion

echo ==========================================
echo VPS Deployment - MAUG Chunking System
echo ==========================================
echo.

REM Konfigürasyon
set VPS_USER=root
set VPS_HOST=173.212.248.71
set VPS_PROJECT_DIR=/root/immunotherapy-api
set BRANCH_NAME=claude/pdf-chunking-embedding-setup-01JLGFuzhLw2pe4uf2SSJbm8

REM VPS bilgilerini kontrol et
if "%VPS_HOST%"=="your-vps-ip-or-hostname" (
    echo [ERROR] Lutfen VPS_HOST degiskenini duzenleyin!
    echo    Script icinde VPS_HOST='your-vps-ip-or-hostname' satirini
    echo    gercek VPS IP adresi veya hostname ile degistirin.
    echo.
    echo Ornek:
    echo    set VPS_HOST=185.123.45.67
    echo    set VPS_HOST=immunotherapy.example.com
    pause
    exit /b 1
)

echo [INFO] Deployment Bilgileri:
echo    VPS: %VPS_USER%@%VPS_HOST%
echo    Dizin: %VPS_PROJECT_DIR%
echo    Branch: %BRANCH_NAME%
echo.

REM Git durumunu kontrol et
echo [CHECK] Git durumu kontrol ediliyor...
git status --porcelain > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git durumu kontrol edilemedi
)

echo.
echo [INFO] VPS'ye baglanmak icin SSH kullanilacak...
echo [INFO] SSH key'inizin kurulu olduguna emin olun!
echo.

set /p confirm="Deployment'a devam etmek istiyor musunuz? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Islem iptal edildi.
    pause
    exit /b 0
)

echo.
echo [DEPLOY] VPS'de deployment basliyor...
echo.

REM SSH ile VPS'de komut çalıştır
ssh %VPS_USER%@%VPS_HOST% "cd %VPS_PROJECT_DIR% && bash /root/immunotherapy-api/vps_update.sh"

if errorlevel 1 (
    echo.
    echo [ERROR] Deployment sirasinda hata olustu!
    echo.
    echo Cozumler:
    echo   1. SSH baglantisini kontrol edin
    echo   2. VPS'de vps_update.sh scriptini kontrol edin
    echo   3. Manuel olarak SSH ile baglanip komutlari calistirin
    pause
    exit /b 1
)

echo.
echo ==========================================
echo [OK] Deployment basariyla tamamlandi!
echo ==========================================
echo.
echo [INFO] Sonraki adimlar (VPS'de):
echo.
echo 1. VPS'ye baglanin:
echo    ssh %VPS_USER%@%VPS_HOST%
echo.
echo 2. Proje dizinine gidin:
echo    cd %VPS_PROJECT_DIR%
echo.
echo 3. Test calistirin:
echo    source venv/bin/activate
echo    python test_maug_chunks.py
echo.
echo 4. Tam indexleme yapin:
echo    ./run_maug_index.sh
echo.
pause
