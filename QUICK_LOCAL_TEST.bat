@echo off
REM MAUG PDF Chunking - Windows Quick Test
REM D:\yazilim\immünoterapi-ai\ klasöründe çalıştırın

echo ================================
echo MAUG PDF Chunking - Quick Test
echo ================================

REM 1. Sanal ortam oluştur
echo.
echo [1/6] Sanal ortam olusturuluyor...
python -m venv venv
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    pause
    exit /b 1
)

REM 2. Sanal ortamı aktive et
echo.
echo [2/6] Sanal ortam aktive ediliyor...
call venv\Scripts\activate.bat

REM 3. Bağımlılıkları yükle
echo.
echo [3/6] Bagimliliklar yukleniyor...
pip install --upgrade pip
pip install -r requirements.txt

REM 4. .env kontrolü
echo.
echo [4/6] .env dosyasi kontrol ediliyor...
if not exist .env (
    echo .env dosyasi bulunamadi!
    copy .env.example .env
    echo UYARI: .env.example kopyalandi.
    echo Lutfen .env dosyasini duzenleyip OPENAI_API_KEY ekleyin!
    notepad .env
    pause
)

REM 5. data/ klasörü ve PDF kontrolü
echo.
echo [5/6] PDF kontrol ediliyor...
if not exist data mkdir data

if not exist data\MAUG_2_20221214_EBOOK.pdf (
    if exist MAUG_2_20221214_EBOOK.pdf (
        echo PDF data\ klasorune kopyalaniyor...
        copy MAUG_2_20221214_EBOOK.pdf data\
    ) else (
        echo HATA: MAUG_2_20221214_EBOOK.pdf bulunamadi!
        echo Lutfen PDF'i su konumlardan birine koyun:
        echo   - %CD%\data\MAUG_2_20221214_EBOOK.pdf
        echo   - %CD%\MAUG_2_20221214_EBOOK.pdf
        pause
        exit /b 1
    )
)

REM 6. Çalıştır
echo.
echo [6/6] MAUG chunking baslatiluyor...
echo.
echo ================================
echo Islem basladi! (~5-10 dakika)
echo ================================
echo.

python process_maug.py

echo.
echo ================================
echo Islem tamamlandi!
echo Cikti: maug_chunks.jsonl
echo ================================
echo.

REM JSONL'i göster
if exist maug_chunks.jsonl (
    echo Ilk 5 chunk:
    powershell -Command "Get-Content maug_chunks.jsonl -TotalCount 5"
    echo.
    echo Toplam chunk sayisi:
    powershell -Command "(Get-Content maug_chunks.jsonl | Measure-Object -Line).Lines"
)

pause
