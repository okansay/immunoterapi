@echo off
REM MAUG API Hizli Test Scripti (Windows)

set API_URL=http://localhost:8000

echo ============================================
echo MAUG API Test
echo ============================================

REM 1. Health check
echo.
echo 1. Health Check...
curl -s "%API_URL%/health"
echo.

REM 2. Test queries
echo.
echo 2. Test Sorgulari...
echo.

REM Test 1: Peanut allergens
echo Test 1: Peanut allergens
curl -s -X POST "%API_URL%/api/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"What are the main allergen components in peanuts?\", \"language\": \"en\"}"
echo.
echo ---
echo.

REM Test 2: Milk allergy
echo Test 2: Milk allergy
curl -s -X POST "%API_URL%/api/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"What are the milk allergen components?\", \"language\": \"en\"}"
echo.
echo ---
echo.

REM Test 3: Basophil test
echo Test 3: Basophil activation test
curl -s -X POST "%API_URL%/api/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"How to perform basophil activation test?\", \"language\": \"en\"}"
echo.
echo ---
echo.

REM Test 4: Profilins (Turkish)
echo Test 4: Profilinler (Turkce)
curl -s -X POST "%API_URL%/api/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"Profilinler nedir ve hangi bitkilerde bulunur?\", \"language\": \"tr\"}"
echo.

echo.
echo ============================================
echo OK: Test tamamlandi!
echo ============================================
pause
