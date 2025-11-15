@echo off
REM MAUG full indexing - Tüm chunk'ları Qdrant'a yükler

echo ==========================================
echo MAUG Full Indexing
echo ==========================================
echo.
echo [UYARI] Bu islem:
echo    - 57 chunk olusturacak
echo    - OpenAI API kullanacak (embedding)
echo    - Qdrant'a yukleyecek
echo    - ~20-30 saniye surecek
echo.

set /p confirm="Devam etmek istiyor musunuz? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Islem iptal edildi.
    pause
    exit /b 0
)

REM Sanal ortamı aktif et
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [ERROR] venv bulunamadi!
    pause
    exit /b 1
)

REM Qdrant kontrolü
echo.
echo [CHECK] Qdrant baglantisi kontrol ediliyor...
curl -s http://localhost:6333/collections >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Qdrant calisiyor
) else (
    echo [ERROR] Qdrant'a baglanilamadi!
    echo    Lutfen Qdrant'i baslatin: docker-compose up -d
    pause
    exit /b 1
)

REM Ana script çalıştır
echo.
python index_maug_chapters.py

echo.
echo ==========================================
echo [OK] Islem tamamlandi!
echo ==========================================
echo.
echo Qdrant collection bilgisi icin:
echo   curl http://localhost:6333/collections/maug
echo.
pause
