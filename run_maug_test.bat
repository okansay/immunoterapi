@echo off
REM MAUG chunk test scripti - İlk 3 chunk'ı gösterir

echo ==========================================
echo MAUG Chunk Test
echo ==========================================
echo.

REM Sanal ortamı aktif et
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [ERROR] venv bulunamadi! Lutfen once 'python -m venv venv' calistirin.
    pause
    exit /b 1
)

REM Test scripti çalıştır
python test_maug_chunks.py

echo.
echo [OK] Test tamamlandi!
echo.
echo Tum chunk'lari indexlemek icin:
echo   run_maug_index.bat
echo.
pause
