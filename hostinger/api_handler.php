<?php
/**
 * API Handler for Immunotherapy Decision Support System
 *
 * This file handles communication between the frontend and the FastAPI backend
 * running on Contabo VPS.
 */

// CORS Headers - Adjust in production for security
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode([
        'success' => false,
        'error' => 'Sadece POST istekleri kabul edilir.'
    ]);
    exit();
}

// Backend API configuration
define('BACKEND_URL', 'http://173.212.248.71:8000/api/query');
define('TIMEOUT', 120); // 120 seconds timeout (GPT-5 için optimize edildi)

/**
 * Send request to FastAPI backend
 */
function sendToBackend($data) {
    $ch = curl_init(BACKEND_URL);

    // Prepare request data
    $jsonData = json_encode($data);

    // cURL options
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $jsonData,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => TIMEOUT,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Content-Length: ' . strlen($jsonData)
        ],
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 3,
    ]);

    // Execute request
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlError = curl_error($ch);
    $curlErrno = curl_errno($ch);

    curl_close($ch);

    // Check for cURL errors
    if ($curlErrno !== 0) {
        return [
            'success' => false,
            'error' => "Bağlantı hatası: " . $curlError,
            'error_code' => 'CURL_ERROR',
            'details' => [
                'errno' => $curlErrno,
                'error' => $curlError
            ]
        ];
    }

    // Check HTTP status code
    if ($httpCode !== 200) {
        $errorMsg = "Sunucu hatası (HTTP $httpCode)";

        // Try to parse error response
        if ($response) {
            $decodedResponse = json_decode($response, true);
            if (json_last_error() === JSON_ERROR_NONE && isset($decodedResponse['detail'])) {
                $errorMsg .= ": " . $decodedResponse['detail'];
            }
        }

        return [
            'success' => false,
            'error' => $errorMsg,
            'error_code' => 'HTTP_ERROR',
            'http_code' => $httpCode
        ];
    }

    // Parse response
    $decodedResponse = json_decode($response, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        return [
            'success' => false,
            'error' => 'Sunucu cevabı işlenemedi: ' . json_last_error_msg(),
            'error_code' => 'JSON_DECODE_ERROR'
        ];
    }

    return [
        'success' => true,
        'data' => $decodedResponse
    ];
}

/**
 * Validate input data
 */
function validateInput($data) {
    $errors = [];

    if (!isset($data['question']) || empty(trim($data['question']))) {
        $errors[] = 'Soru alanı boş olamaz.';
    } elseif (strlen($data['question']) > 1000) {
        $errors[] = 'Soru en fazla 1000 karakter olabilir.';
    }

    if (!isset($data['language']) || !in_array($data['language'], ['tr', 'en'])) {
        $errors[] = 'Geçersiz dil seçimi. "tr" veya "en" olmalıdır.';
    }

    return $errors;
}

/**
 * Sanitize input
 */
function sanitizeInput($data) {
    return [
        'question' => trim($data['question']),
        'language' => $data['language']
    ];
}

/**
 * Log request (optional - for debugging)
 */
function logRequest($data, $response) {
    // Uncomment below for debugging
    // $logFile = __DIR__ . '/logs/api_requests.log';
    // $logDir = dirname($logFile);
    // if (!is_dir($logDir)) {
    //     mkdir($logDir, 0755, true);
    // }
    //
    // $logEntry = [
    //     'timestamp' => date('Y-m-d H:i:s'),
    //     'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    //     'request' => $data,
    //     'success' => $response['success']
    // ];
    //
    // file_put_contents($logFile, json_encode($logEntry) . PHP_EOL, FILE_APPEND);
}

// Main execution
try {
    // Get raw POST data
    $rawInput = file_get_contents('php://input');

    if (empty($rawInput)) {
        throw new Exception('İstek verisi boş.');
    }

    // Parse JSON input
    $inputData = json_decode($rawInput, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception('Geçersiz JSON formatı: ' . json_last_error_msg());
    }

    // Validate input
    $validationErrors = validateInput($inputData);

    if (!empty($validationErrors)) {
        http_response_code(400);
        echo json_encode([
            'success' => false,
            'error' => implode(' ', $validationErrors),
            'error_code' => 'VALIDATION_ERROR'
        ]);
        exit();
    }

    // Sanitize input
    $sanitizedData = sanitizeInput($inputData);

    // Send to backend
    $result = sendToBackend($sanitizedData);

    // Log request (optional)
    logRequest($sanitizedData, $result);

    // Return response
    if ($result['success']) {
        http_response_code(200);
        echo json_encode($result);
    } else {
        http_response_code(500);
        echo json_encode($result);
    }

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage(),
        'error_code' => 'EXCEPTION'
    ]);
}
?>
