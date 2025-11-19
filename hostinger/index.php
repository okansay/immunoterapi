<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İmmünoterapi Karar Destek Sistemi</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }

        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            color: #666;
            font-size: 1.1em;
        }

        .main-card {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 10px;
            color: #333;
            font-weight: 600;
            font-size: 1.1em;
        }

        .form-group textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            font-family: inherit;
            transition: border-color 0.3s;
            resize: vertical;
            min-height: 120px;
        }

        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .language-selector {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .language-selector label {
            margin: 0;
        }

        .radio-group {
            display: flex;
            gap: 20px;
        }

        .radio-option {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }

        .radio-option input[type="radio"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .radio-option span {
            font-size: 1em;
            color: #333;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }

        .loading.active {
            display: block;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .result-card {
            display: none;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
            border-left: 5px solid #667eea;
        }

        .result-card.active {
            display: block;
        }

        .result-card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }

        .answer-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            line-height: 1.8;
            color: #333;
            font-size: 1.05em;
        }

        .sources-section h3 {
            color: #764ba2;
            margin-bottom: 15px;
            font-size: 1.4em;
        }

        .source-item {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #764ba2;
        }

        .source-item .source-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .source-item .source-title {
            font-weight: 600;
            color: #333;
            font-size: 1.1em;
        }

        .source-item .relevance-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }

        .source-item .source-details {
            color: #666;
            font-size: 0.95em;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .source-detail-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .source-detail-item strong {
            color: #333;
        }

        .processing-time {
            text-align: right;
            color: #999;
            font-size: 0.9em;
            margin-top: 15px;
        }

        .error-card {
            display: none;
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            color: #856404;
        }

        .error-card.active {
            display: block;
        }

        .error-card h3 {
            margin-bottom: 10px;
            color: #dc3545;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            .main-card {
                padding: 25px;
            }

            .source-item .source-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }

        .examples {
            background: #e8eaf6;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }

        .examples h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }

        .example-btn {
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.95em;
        }

        .example-btn:hover {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 İmmünoterapi Karar Destek Sistemi</h1>
            <p>Bilimsel kaynaklara dayalı, yapay zeka destekli tıbbi bilgi sistemi</p>
        </div>

        <div class="main-card">
            <form id="queryForm">
                <div class="examples">
                    <h3>📋 Örnek Sorular (Tıklayarak Kullanabilirsiniz)</h3>
                    <button type="button" class="example-btn" onclick="useExample('PD-1 ve PD-L1 inhibitörleri arasındaki farklar nelerdir?')">PD-1 vs PD-L1 inhibitörleri</button>
                    <button type="button" class="example-btn" onclick="useExample('Melanom tedavisinde hangi immünoterapi ajanları kullanılır?')">Melanom immünoterapisi</button>
                    <button type="button" class="example-btn" onclick="useExample('CAR-T hücre tedavisinin yan etkileri nelerdir?')">CAR-T yan etkileri</button>
                    <button type="button" class="example-btn" onclick="useExample('What are the mechanisms of immune checkpoint inhibitors?')">Checkpoint inhibitors (EN)</button>
                </div>

                <div class="form-group">
                    <label for="question">💬 Sorunuzu Girin:</label>
                    <textarea
                        id="question"
                        name="question"
                        placeholder="Örneğin: PD-1 inhibitörleri hangi kanser türlerinde etkilidir?"
                        required
                    ></textarea>
                </div>

                <div class="form-group">
                    <div class="language-selector">
                        <label>🌐 Cevap Dili:</label>
                        <div class="radio-group">
                            <label class="radio-option">
                                <input type="radio" name="language" value="tr" checked>
                                <span>Türkçe</span>
                            </label>
                            <label class="radio-option">
                                <input type="radio" name="language" value="en">
                                <span>English</span>
                            </label>
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn" id="submitBtn">
                    🔍 Sorgula
                </button>
            </form>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Sorgunuz işleniyor, lütfen bekleyin...</p>
            </div>

            <div class="error-card" id="errorCard">
                <h3>⚠️ Hata Oluştu</h3>
                <p id="errorMessage"></p>
            </div>
        </div>

        <div class="result-card" id="resultCard">
            <h2>📊 Analiz Sonucu</h2>
            <div class="answer-section" id="answerSection"></div>

            <div class="sources-section">
                <h3>📚 Kaynaklar</h3>
                <div id="sourcesContainer"></div>
            </div>

            <div class="processing-time" id="processingTime"></div>
        </div>

        <div class="footer">
            <p>© 2025 İmmünoterapi Karar Destek Sistemi | Powered by OpenAI & Qdrant</p>
            <p style="font-size: 0.9em; margin-top: 10px; opacity: 0.8;">
                ⚠️ Bu sistem sadece bilgilendirme amaçlıdır. Tıbbi kararlar için mutlaka uzman hekime danışın.
            </p>
        </div>
    </div>

    <script>
        function useExample(text) {
            document.getElementById('question').value = text;
            // İngilizce örnek ise dili otomatik değiştir
            if (text.toLowerCase().includes('what') || text.toLowerCase().includes('how')) {
                document.querySelector('input[name="language"][value="en"]').checked = true;
            }
        }

        document.getElementById('queryForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const question = document.getElementById('question').value.trim();
            const language = document.querySelector('input[name="language"]:checked').value;

            if (!question) {
                showError('Lütfen bir soru girin.');
                return;
            }

            // UI güncellemeleri
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('loading').classList.add('active');
            document.getElementById('resultCard').classList.remove('active');
            document.getElementById('errorCard').classList.remove('active');

            try {
                const response = await fetch('api_handler.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: question,
                        language: language
                    })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    displayResults(data.data);
                } else {
                    showError(data.error || 'Bilinmeyen bir hata oluştu.');
                }
            } catch (error) {
                showError('Sunucuya bağlanırken hata oluştu: ' + error.message);
            } finally {
                document.getElementById('submitBtn').disabled = false;
                document.getElementById('loading').classList.remove('active');
            }
        });

        function displayResults(data) {
            // Cevabı göster
            document.getElementById('answerSection').innerHTML = formatAnswer(data.answer);

            // Kaynakları göster
            const sourcesContainer = document.getElementById('sourcesContainer');
            sourcesContainer.innerHTML = '';

            if (data.sources && data.sources.length > 0) {
                data.sources.forEach((source, index) => {
                    const sourceDiv = document.createElement('div');
                    sourceDiv.className = 'source-item';
                    sourceDiv.innerHTML = `
                        <div class="source-header">
                            <div class="source-title">📖 Kaynak ${index + 1}</div>
                            <div class="relevance-badge">İlgililik: ${(source.relevance_score * 100).toFixed(1)}%</div>
                        </div>
                        <div class="source-details">
                            <div class="source-detail-item">
                                <strong>Bölüm:</strong> ${escapeHtml(source.chapter || 'N/A')}
                            </div>
                            <div class="source-detail-item">
                                <strong>Alt Bölüm:</strong> ${escapeHtml(source.subsection || 'N/A')}
                            </div>
                            <div class="source-detail-item">
                                <strong>Sayfa:</strong> ${escapeHtml(source.page || 'N/A')}
                            </div>
                        </div>
                    `;
                    sourcesContainer.appendChild(sourceDiv);
                });
            } else {
                sourcesContainer.innerHTML = '<p style="color: #999;">Kaynak bilgisi bulunamadı.</p>';
            }

            // İşlem süresini göster
            document.getElementById('processingTime').textContent =
                `⏱️ İşlem süresi: ${data.processing_time ? data.processing_time.toFixed(2) : 'N/A'} saniye`;

            // Sonuç kartını göster
            document.getElementById('resultCard').classList.add('active');

            // Sonuç kartına scroll
            document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function formatAnswer(answer) {
            // Satır sonlarını <br> ile değiştir
            let formatted = escapeHtml(answer).replace(/\n/g, '<br>');

            // Kalın yazıları formatla (örn: **text** -> <strong>text</strong>)
            formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

            // Liste işaretlerini formatla
            formatted = formatted.replace(/^- (.+)$/gm, '• $1');

            return formatted;
        }

        function showError(message) {
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('errorCard').classList.add('active');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
