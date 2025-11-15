# MAUG PDF Chunking Configuration
# Bu dosyayı kopyalayın: cp maug_config.example.py maug_config.py
# Ardından process_maug.py içinde import edin (opsiyonel)

# PDF Paths
PDF_PATH = "data/MAUG_2_20221214_EBOOK.pdf"
OUTPUT_JSONL = "maug_chunks.jsonl"

# LLM Settings
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 2000

# Segmentation Parameters
MIN_CHARS = 2000      # Minimum segment uzunluğu (karakter)
MAX_CHARS = 8000      # Maximum segment uzunluğu (karakter)
TARGET_WORDS = 800    # Hedef kelime sayısı (LLM'e önerilir)
MIN_WORDS_TO_SEGMENT = 300  # Bundan kısa chapter'lar bölünmez

# Chapter Pattern (regex)
# MAUG için: A01, B02, C11, D03 formatı
# Farklı PDF için değiştirin
CHAPTER_PATTERN_STR = r"^([ABCD]\d{2})\s*[–-]\s*(.+)$"

# Processing Options
INCLUDE_PREFACE = True     # İlk chapter'dan önce preface chunk'ı oluştur
RATE_LIMIT_DELAY = 0.5     # LLM çağrıları arası bekleme (saniye)

# Fallback Segmentation (LLM başarısız olursa)
FALLBACK_NUM_SEGMENTS = 3  # Basit bölme için segment sayısı

# Debug/Logging
VERBOSE = True             # Detaylı log çıktısı
SAVE_INTERMEDIATE = False  # Ara sonuçları kaydet (debug için)

# Output Options
JSONL_INDENT = None        # JSONL indent (None = compact, 2 = pretty)
INCLUDE_PAGE_MARKERS = True  # text alanında [[PAGE_X]] marker'larını tut
