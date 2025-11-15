@echo off
REM MAUG Hizli Kurulum Scripti (Windows)

echo ============================================
echo MAUG PDF -^> Qdrant Hizli Kurulum
echo ============================================

REM 1. .env kontrolu
echo.
echo 1. .env dosyasi kontrol ediliyor...
if not exist .env (
    echo    .env dosyasi bulunamadi, olusturuluyor...
    copy .env.example .env
    echo    WARNING: .env dosyasini duzenleyin ve OPENAI_API_KEY ekleyin!
    echo    Sonra bu scripti tekrar calistirin.
    pause
    exit /b 1
)

findstr /C:"your_openai_api_key_here" .env >nul
if %errorlevel%==0 (
    echo    ERROR: OPENAI_API_KEY henuz eklenmemis!
    echo    Lutfen .env dosyasini duzenleyin.
    pause
    exit /b 1
)
echo    OK: .env dosyasi hazir

REM 2. PDF kontrolu
echo.
echo 2. PDF dosyasi kontrol ediliyor...
if not exist data\MAUG_2_20221214_EBOOK.pdf (
    echo    ERROR: PDF bulunamadi: data\MAUG_2_20221214_EBOOK.pdf
    echo    Lutfen PDF'i data\ klasorune kopyalayin.
    pause
    exit /b 1
)
echo    OK: PDF hazir

REM 3. Python paketleri
echo.
echo 3. Python paketleri kontrol ediliyor...
python -c "import fitz" 2>nul
if %errorlevel% neq 0 (
    echo    PyMuPDF kurulu degil, kuruluyor...
    pip install PyMuPDF==1.23.8
)
echo    OK: Python paketleri hazir

REM 4. Qdrant kontrolu
echo.
echo 4. Qdrant kontrol ediliyor...
curl -s http://localhost:6333/collections >nul 2>&1
if %errorlevel% neq 0 (
    echo    WARNING: Qdrant calismiyor!
    echo    Lutfen Docker ile Qdrant'i baslatin:
    echo    docker run -d -p 6333:6333 -p 6334:6334 -v %CD%\qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
    pause
    exit /b 1
)
echo    OK: Qdrant calisiyor

REM 5. Collection olustur
echo.
echo 5. Qdrant collection olusturuluyor...
python init_qdrant.py
echo    OK: Collection hazir

REM 6. PDF'i indexle
echo.
echo 6. PDF indexleniyor ve Qdrant'a yukleniyor...
echo    (Bu islem ~5-7 dakika surebilir)
python index_maug_direct.py

REM 7. Bitti
echo.
echo ============================================
echo OK: Kurulum tamamlandi!
echo ============================================
echo.
echo API'yi baslatmak icin:
echo   python main.py
echo.
echo Test etmek icin:
echo   curl http://localhost:8000/health
echo.
pause
