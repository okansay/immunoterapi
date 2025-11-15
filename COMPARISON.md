# İki İndexleme Yöntemi Karşılaştırması

## 📊 Yöntem 1: `index_book.py` (Eski - Her Chunk için LLM)

### Nasıl Çalışır?
1. PDF'i chunk'lara böler
2. **Her chunk için GPT-4o-mini'ye sorar**: "Bu chunk hangi chapter'a ait?"
3. Embedding oluşturur
4. Qdrant'a kaydeder

### Avantajları ✅
- Basit implementasyon
- Her chunk için detaylı analiz

### Dezavantajları ❌
- **Çok maliyetli**: 500 chunk × $0.15 / 1M token ≈ $2-5
- **Yavaş**: Her chunk için LLM çağrısı (~30-60 dakika)
- **Tutarsız**: Aynı chapter farklı isimlendirebilir
- **Tablo/şekil bütünlüğü yok**: Tablo ortasında chunk kesilir
- **Chapter boundary bilinmez**: Chapter ortasında chunk kesebilir

### Örnek Maliyet (576 sayfa kitap)
```
- Chunk sayısı: ~500-600
- LLM çağrısı: 500 × (500 token input + 50 token output)
- Maliyet: ~$3-5
- Süre: ~45-60 dakika
```

---

## 🚀 Yöntem 2: `index_book_smart.py` (Yeni - TOC + Akıllı Chunking)

### Nasıl Çalışır?
1. **TOC Extraction** (Table of Contents çıkarımı):
   - Önce PDF bookmark/outline yapısını okur
   - Bookmark yoksa → İlk 20 sayfayı LLM'e gösterip **1 kez** TOC çıkarır
   - Her chapter'ın sayfa aralığını belirler

2. **Chapter Mapping Oluşturur**:
   ```python
   {
       1: ("Chapter 1: Introduction", "N/A"),
       2: ("Chapter 1: Introduction", "N/A"),
       ...
       45: ("Chapter 2: T-Cell Biology", "N/A"),
       ...
   }
   ```

3. **Akıllı Chunking**:
   - Sayfa numarasına göre chapter'ı otomatik ekler
   - Chapter değişiminde chunk'ı keser (chapter ortasında kesme yok!)
   - Tablo/şekil tespiti yapar ve bütün tutar
   - Normal paragraflar için overlap uygular

4. Embedding oluşturur ve Qdrant'a kaydeder

### Avantajları ✅
- **%95 daha ucuz**: Sadece 1 LLM çağrısı (TOC için)
- **%90 daha hızlı**: LLM çağrısı minimumda
- **Tutarlı chapter isimleri**: TOC'dan geldiği için
- **Tablo/şekil koruması**: `is_table_or_figure()` ile tespit
- **Chapter boundary awareness**: Chapter değişiminde chunk kesilir
- **Daha iyi semantik**: İlgili içerik bir arada

### Örnek Maliyet (576 sayfa kitap)
```
- LLM çağrısı: 1 × (4000 token TOC extraction)
- Maliyet: ~$0.05-0.10
- Süre: ~5-10 dakika
```

---

## 🔬 Teknik Detaylar

### TOC Extraction Stratejisi

#### 1. Öncelik: PDF Bookmarks
```python
# PyPDF ile outline okuma
reader.outline → {
    "Chapter 1: Introduction": 1,
    "Chapter 2: T-Cell Biology": 45,
    ...
}
```

#### 2. Yedek: LLM ile TOC Çıkarımı
```python
# İlk 20 sayfayı LLM'e gönder (sadece 1 kez!)
prompt = "İçindekiler sayfasından chapter ve sayfa numaralarını çıkar"
→ JSON formatında TOC
```

#### 3. Son çare: Sayfa bazlı gruplama
```python
# Her 20 sayfa bir "Section"
Page 1-20: "Section 1"
Page 21-40: "Section 2"
```

### Tablo/Şekil Tespiti

```python
def is_table_or_figure(text: str) -> bool:
    # Pattern matching
    - "Table 1", "Figure 2", "Tablo 3", "Şekil 4"
    - Tab/boşluk yoğun satırlar (tablo sütunları)
    - Kısa satırlar ama düzenli yapı

    → True ise: Chunk'ı bölme!
```

### Chapter Boundary Handling

```python
# Eski yöntem
Chunk 1: ... Chapter 1 içeriği ...
Chunk 2: ... Chapter 1 sonu + Chapter 2 başı ... ❌

# Yeni yöntem
Chunk 1: ... Chapter 1 içeriği (tamamen) ... ✓
Chunk 2: ... Chapter 2 içeriği (baştan) ... ✓
```

---

## 📈 Performans Karşılaştırması

| Metrik | Eski Yöntem | Yeni Yöntem | İyileştirme |
|--------|-------------|-------------|-------------|
| **Maliyet** | $3-5 | $0.05-0.10 | **%95 azalma** |
| **Süre** | 45-60 dk | 5-10 dk | **%90 azalma** |
| **LLM Çağrısı** | 500-600 | 1 | **%99.8 azalma** |
| **Chapter tutarlılığı** | Düşük | Yüksek | ✅ |
| **Tablo bütünlüğü** | Yok | Var | ✅ |
| **Chapter boundary** | Rastgele | Kontrollü | ✅ |

---

## 🎯 Hangi Yöntemi Kullanmalıyım?

### `index_book.py` kullan eğer:
- PDF'in TOC/bookmark yapısı hiç yoksa
- Çok küçük dokümansa (< 50 sayfa)
- Maliyet önemli değilse
- Her chunk'ın bağlamsal analizi önemliyse

### `index_book_smart.py` kullan eğer: ✅ (ÖNERİLEN)
- **576 sayfalık kitap gibi büyük dokümanlarda**
- Maliyet önemliyse
- Hız önemliyse
- Chapter yapısı düzenli ve önemliyse
- Tablo/şekil bütünlüğü önemliyse
- **Production ortamında kullanacaksan**

---

## 💡 Kullanım Örnekleri

### Yöntem 1 (Eski)
```bash
python index_book.py
# Bekleme: ~45-60 dakika
# Maliyet: ~$3-5
```

### Yöntem 2 (Yeni - Önerilen)
```bash
python index_book_smart.py
# Bekleme: ~5-10 dakika
# Maliyet: ~$0.05-0.10
```

---

## 🔍 Sonuç

**`index_book_smart.py` kullanın!**

Hem daha hızlı, hem daha ucuz, hem de daha kaliteli chunking sağlıyor.

### Tek istisna:
PDF'in hiç TOC/bookmark yapısı yoksa ve içindekiler sayfası da yoksa,
`index_book.py` kullanmak zorunda kalabilirsiniz. Ama bu çok nadir bir durum.
