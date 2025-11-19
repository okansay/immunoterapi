# İmmünoterapi Karar Destek Sistemi - Hostinger Arayüzü

Modern, kullanıcı dostu PHP web arayüzü. Contabo VPS üzerindeki FastAPI backend ile iletişim kurar.

## 📁 Dosyalar

```
hostinger/
├── index.php          # Ana web arayüzü (HTML/CSS/JavaScript dahil)
├── api_handler.php    # Backend ile iletişim kuran API handler
├── .htaccess          # Apache yapılandırması (opsiyonel)
└── README.md          # Bu dosya
```

## 🚀 Kurulum

### 1. Hostinger'a Dosya Yükleme

#### Yöntem A: File Manager (Web Arayüzü)
1. Hostinger kontrolpanel'e giriş yapın
2. **File Manager**'ı açın
3. `public_html` klasörüne gidin
4. Aşağıdaki dosyaları yükleyin:
   - `index.php`
   - `api_handler.php`
   - `.htaccess` (opsiyonel)

#### Yöntem B: FTP (FileZilla vb.)
1. FTP bilgilerinizi Hostinger'dan alın
2. FileZilla veya benzeri FTP istemcisi ile bağlanın
3. `public_html` dizinine dosyaları yükleyin

### 2. Dizin Yapısı

Yükleme sonrası `public_html` içindeki yapı:

```
public_html/
├── index.php
├── api_handler.php
└── .htaccess (opsiyonel)
```

### 3. İzin Ayarları

Dosya izinleri (gerekirse):
```
index.php        -> 644 (rw-r--r--)
api_handler.php  -> 644 (rw-r--r--)
.htaccess        -> 644 (rw-r--r--)
```

## ⚙️ Yapılandırma

### Backend URL Değiştirme

Eğer VPS IP adresi değişirse, `api_handler.php` dosyasında şu satırı güncelleyin:

```php
define('BACKEND_URL', 'http://173.212.248.71/api/query');
```

Yeni IP:
```php
define('BACKEND_URL', 'http://YENİ_IP_ADRESİ/api/query');
```

### Timeout Süresi Ayarlama

Uzun sorgular için timeout süresini artırabilirsiniz:

```php
define('TIMEOUT', 60); // Saniye cinsinden
```

## 🔒 Güvenlik (Üretim Ortamı İçin)

### 1. CORS Kısıtlaması

`api_handler.php` içinde tüm domainlere izin veriliyor:

```php
header('Access-Control-Allow-Origin: *');
```

**Üretim için** sadece kendi domaininize izin verin:

```php
header('Access-Control-Allow-Origin: https://yourdomain.com');
```

### 2. HTTPS Kullanımı

SSL sertifikası aktifleştirin:
- Hostinger'da **SSL/TLS** bölümünden ücretsiz Let's Encrypt sertifikası kurun
- `.htaccess` dosyasındaki HTTPS yönlendirmesini aktif edin

### 3. Rate Limiting (İsteğe Bağlı)

`api_handler.php` içinde basit rate limiting ekleyebilirsiniz:

```php
// Örnek: IP başına 10 istek/dakika limiti
// Bu kısmı gerekirse kendiniz implement edebilirsiniz
```

## 🧪 Test

### 1. Web Tarayıcı ile Test

1. `https://yourdomain.com` veya `https://yourdomain.com/index.php` adresine gidin
2. Örnek bir soru girin:
   ```
   PD-1 ve PD-L1 inhibitörleri arasındaki farklar nelerdir?
   ```
3. "Sorgula" butonuna tıklayın
4. Sonuçları kontrol edin

### 2. Backend Bağlantısı Test

Tarayıcı geliştirici araçlarını (F12) açın ve Network sekmesinde:
- `api_handler.php` isteğini kontrol edin
- Status: 200 OK olmalı
- Response JSON formatında gelmelidir

### 3. Manuel API Test (cURL)

```bash
curl -X POST https://yourdomain.com/api_handler.php \
  -H "Content-Type: application/json" \
  -d '{
    "question": "PD-1 nedir?",
    "language": "tr"
  }'
```

## 🐛 Hata Ayıklama

### Log Kayıtları Aktifleştirme

`api_handler.php` içinde `logRequest()` fonksiyonundaki yorum satırlarını kaldırın:

```php
function logRequest($data, $response) {
    $logFile = __DIR__ . '/logs/api_requests.log';
    $logDir = dirname($logFile);
    if (!is_dir($logDir)) {
        mkdir($logDir, 0755, true);
    }

    $logEntry = [
        'timestamp' => date('Y-m-d H:i:s'),
        'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        'request' => $data,
        'success' => $response['success']
    ];

    file_put_contents($logFile, json_encode($logEntry) . PHP_EOL, FILE_APPEND);
}
```

### Yaygın Hatalar ve Çözümleri

#### 1. "Sunucuya bağlanırken hata oluştu"
- **Sebep**: VPS erişilemiyor
- **Çözüm**:
  - VPS'in çalıştığından emin olun
  - IP adresini kontrol edin
  - FastAPI uygulamasının çalıştığını doğrulayın

#### 2. "HTTP 500 Internal Server Error"
- **Sebep**: PHP hatası
- **Çözüm**:
  - PHP error_log dosyasını kontrol edin
  - Hostinger File Manager'da `error_log` dosyasına bakın

#### 3. "CORS hatası"
- **Sebep**: Cross-origin resource sharing engeli
- **Çözüm**:
  - `api_handler.php` içinde CORS header'larını kontrol edin

#### 4. "Timeout hatası"
- **Sebep**: Backend yanıt vermiyor veya çok yavaş
- **Çözüm**:
  - Timeout süresini artırın
  - Backend'in çalıştığından emin olun

## 📊 Özellikler

✅ Responsive tasarım (mobil uyumlu)
✅ Türkçe/İngilizce dil desteği
✅ Örnek sorular ile hızlı test
✅ Loading indicator
✅ Detaylı kaynak bilgisi gösterimi
✅ İlgililik skorları
✅ İşlem süresi gösterimi
✅ Hata yönetimi
✅ Modern, profesyonel arayüz

## 🔄 Güncelleme

Dosyaları güncellemek için:

1. Yeni versiyonları indirin
2. Mevcut dosyaların yedeğini alın
3. Yeni dosyaları yükleyin
4. Tarayıcı cache'ini temizleyin (Ctrl+F5)

## 📞 Destek

Sorun yaşarsanız:

1. **Backend durumu kontrol**: `http://173.212.248.71/health`
2. **PHP error_log** dosyasını kontrol edin
3. **Tarayıcı console** (F12) hatalarını kontrol edin

## 📝 Notlar

- Sistem sadece bilgilendirme amaçlıdır
- Tıbbi kararlar için mutlaka uzman hekime danışılmalıdır
- Backend VPS'in sürekli çalışır durumda olması gerekmektedir

## 🌐 Erişim

Kurulum tamamlandıktan sonra aşağıdaki URL'lerden erişebilirsiniz:

- **Ana sayfa**: `https://yourdomain.com` veya `https://yourdomain.com/index.php`
- **API endpoint**: `https://yourdomain.com/api_handler.php` (sadece POST)

---

**Oluşturulma Tarihi**: 2025-11-15
**Backend**: FastAPI @ Contabo VPS (173.212.248.71)
**Frontend**: PHP @ Hostinger
