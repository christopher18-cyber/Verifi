document.addEventListener('DOMContentLoaded', () => {
    // Core Elements
    const form = document.getElementById('scan-form');
    const messageInput = document.getElementById('message-input');
    const submitBtn = document.getElementById('submit-btn');
    const verdictPill = document.getElementById('verdict-pill');
    const pipelineSteps = document.getElementById('pipeline-steps');
    const detailsBox = document.getElementById('details-box');
    const scoreBadge = document.getElementById('score-badge');
    const flagsContainer = document.getElementById('flags-container');
    const reasonText = document.getElementById('reason-text');

    // Tab & OCR Elements
    const tabTextBtn = document.getElementById('tab-text-btn');
    const tabOcrBtn = document.getElementById('tab-ocr-btn');
    const ocrContainer = document.getElementById('ocr-container');
    const ocrDropzone = document.getElementById('ocr-dropzone');
    const ocrFileInput = document.getElementById('ocr-file-input');
    const ocrPreviewCard = document.getElementById('ocr-preview-card');
    const ocrPreviewImg = document.getElementById('ocr-preview-img');
    const ocrFileName = document.getElementById('ocr-file-name');
    const ocrFileSize = document.getElementById('ocr-file-size');
    const ocrProgressBox = document.getElementById('ocr-progress-box');
    const ocrProgressBar = document.getElementById('ocr-progress-bar');
    const ocrPercentText = document.getElementById('ocr-percent-text');
    const ocrStatusText = document.getElementById('ocr-status-text');
    const ocrSuccessAlert = document.getElementById('ocr-success-alert');
    const ocrCharCount = document.getElementById('ocr-char-count');
    const ocrRescanBtn = document.getElementById('ocr-rescan-btn');
    const ocrClearBtn = document.getElementById('ocr-clear-btn');

    let currentLang = 'en';
    let currentImageFile = null;
    let currentPreviewUrl = null;
    let isOcrProcessing = false;

    // --- TAB SWITCHING ---
    function activateTextTab() {
        tabTextBtn.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
        tabTextBtn.classList.remove('text-slate-500');
        tabOcrBtn.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
        tabOcrBtn.classList.add('text-slate-500');
        ocrContainer.classList.add('hidden');
    }

    function activateOcrTab() {
        tabOcrBtn.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
        tabOcrBtn.classList.remove('text-slate-500');
        tabTextBtn.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
        tabTextBtn.classList.add('text-slate-500');
        ocrContainer.classList.remove('hidden');
    }

    tabTextBtn.addEventListener('click', activateTextTab);
    tabOcrBtn.addEventListener('click', activateOcrTab);

    // --- LANGUAGE SWITCHER & MULTI-LINGUAL SUPPORT ---
    const LANG_LABELS = {
        'en': 'English',
        'pidgin': 'Nigerian Pidgin',
        'yoruba': 'Yorùbá',
        'hausa': 'Hausa',
        'igbo': 'Igbo'
    };

    function setLanguage(lang) {
        currentLang = lang;
        document.querySelectorAll('.lang-btn').forEach(b => {
            if (b.getAttribute('data-lang') === lang) {
                b.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
                b.classList.remove('text-slate-500');
            } else {
                b.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
                b.classList.add('text-slate-500');
            }
        });
    }

    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const lang = e.currentTarget.getAttribute('data-lang');
            setLanguage(lang);
        });
    });

    // --- TEXT SAMPLE BUTTONS ---
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            messageInput.value = e.currentTarget.getAttribute('data-msg');
            const sampleLang = e.currentTarget.getAttribute('data-lang');
            if (sampleLang) {
                setLanguage(sampleLang);
            }
            activateTextTab();
            messageInput.focus();
        });
    });

    // --- OCR FILE SELECTION & DRAG AND DROP ---
    ocrDropzone.addEventListener('click', () => {
        if (!isOcrProcessing) {
            ocrFileInput.click();
        }
    });

    ocrFileInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            processImageFile(file);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        ocrDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!isOcrProcessing) {
                ocrDropzone.classList.add('drag-active');
            }
        });
    });

    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
        ocrDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            ocrDropzone.classList.remove('drag-active');
        });
    });

    ocrDropzone.addEventListener('drop', (e) => {
        if (isOcrProcessing) return;
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
            const file = dt.files[0];
            if (file.type.startsWith('image/')) {
                processImageFile(file);
            } else {
                alert('Please upload an image file (PNG, JPG, WebP).');
            }
        }
    });

    // Global Clipboard Paste (Ctrl+V) anywhere on the page
    window.addEventListener('paste', (e) => {
        const items = e.clipboardData && e.clipboardData.items;
        if (!items) return;

        for (let i = 0; i < items.length; i++) {
            if (items[i].type.startsWith('image/')) {
                const file = items[i].getAsFile();
                if (file) {
                    e.preventDefault();
                    activateOcrTab();
                    processImageFile(file, `pasted_screenshot_${Date.now()}.png`);
                    break;
                }
            }
        }
    });

    // --- IMAGE PREVIEW & CLEAR ---
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function clearOcrImage() {
        if (currentPreviewUrl) {
            URL.revokeObjectURL(currentPreviewUrl);
            currentPreviewUrl = null;
        }
        currentImageFile = null;
        ocrFileInput.value = '';
        ocrPreviewCard.classList.add('hidden');
        ocrProgressBox.classList.add('hidden');
        ocrSuccessAlert.classList.add('hidden');
        ocrDropzone.classList.remove('hidden');
        isOcrProcessing = false;
    }

    ocrClearBtn.addEventListener('click', clearOcrImage);

    ocrRescanBtn.addEventListener('click', () => {
        if (currentImageFile && !isOcrProcessing) {
            runOcrOnImage(currentImageFile);
        }
    });

    // --- OCR EXTRACTION CORE VIA TESSERACT.JS ---
    async function processImageFile(fileOrBlob, overrideName = null) {
        if (isOcrProcessing) return;

        currentImageFile = fileOrBlob;
        const name = overrideName || fileOrBlob.name || 'screenshot.png';
        const size = fileOrBlob.size ? formatBytes(fileOrBlob.size) : 'Image';

        // Setup image thumbnail preview
        if (currentPreviewUrl) {
            URL.revokeObjectURL(currentPreviewUrl);
        }
        currentPreviewUrl = URL.createObjectURL(fileOrBlob);
        ocrPreviewImg.src = currentPreviewUrl;
        ocrFileName.textContent = name;
        ocrFileSize.textContent = size;

        ocrDropzone.classList.add('hidden');
        ocrPreviewCard.classList.remove('hidden');
        ocrSuccessAlert.classList.add('hidden');

        await runOcrOnImage(fileOrBlob);
    }

    async function runOcrOnImage(imageSource) {
        if (typeof Tesseract === 'undefined') {
            alert('Tesseract.js OCR library is still loading. Please check your internet connection and try again.');
            return;
        }

        isOcrProcessing = true;
        ocrProgressBox.classList.remove('hidden');
        ocrProgressBar.style.width = '5%';
        ocrPercentText.textContent = '5%';
        ocrStatusText.innerHTML = '<span class="inline-block animate-spin">⏳</span> Initializing vision reader...';
        ocrRescanBtn.disabled = true;

        try {
            const result = await Tesseract.recognize(
                imageSource,
                'eng',
                {
                    logger: (m) => {
                        let pct = 10;
                        if (m.progress) {
                            pct = Math.min(100, Math.max(10, Math.round(m.progress * 100)));
                        }

                        ocrProgressBar.style.width = `${pct}%`;
                        ocrPercentText.textContent = `${pct}%`;

                        if (m.status === 'loading tesseract core') {
                            ocrStatusText.innerHTML = '<span class="inline-block animate-spin">⏳</span> Loading OCR WebAssembly core...';
                        } else if (m.status === 'loading language traineddata') {
                            ocrStatusText.innerHTML = '<span class="inline-block animate-spin">⏳</span> Downloading trained English vision model...';
                        } else if (m.status === 'initializing api') {
                            ocrStatusText.innerHTML = '<span class="inline-block animate-spin">⏳</span> Preparing recognition engine...';
                        } else if (m.status === 'recognizing text') {
                            ocrStatusText.innerHTML = `<span class="inline-block animate-pulse">🔍</span> Scanning screenshot text... ${pct}%`;
                        }
                    }
                }
            );

            const rawText = (result && result.data && result.data.text) ? result.data.text : '';
            const cleanedText = cleanExtractedText(rawText);

            ocrProgressBar.style.width = '100%';
            ocrPercentText.textContent = '100%';

            if (cleanedText.length > 0) {
                messageInput.value = cleanedText;
                ocrProgressBox.classList.add('hidden');
                ocrSuccessAlert.classList.remove('hidden');
                ocrCharCount.textContent = `Extracted ${cleanedText.length} characters from screenshot`;

                // Flash textarea border to signal text has been imported
                messageInput.classList.add('ring-2', 'ring-indigo-500');
                setTimeout(() => messageInput.classList.remove('ring-2', 'ring-indigo-500'), 1500);
            } else {
                ocrStatusText.innerHTML = '⚠️ No readable text detected. Please ensure the screenshot is clear.';
                ocrProgressBar.style.width = '0%';
                ocrPercentText.textContent = '0%';
            }

        } catch (err) {
            console.error('OCR Processing Error:', err);
            ocrStatusText.innerHTML = `<span class="text-red-600">❌ Error extracting text: ${escapeHtml(err.message || 'Unknown error')}</span>`;
        } finally {
            isOcrProcessing = false;
            ocrRescanBtn.disabled = false;
        }
    }

    function cleanExtractedText(text) {
        return text
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .join(' ')
            .replace(/\s{2,}/g, ' ')
            .trim();
    }

    // --- FORM SUBMISSION & HYBRID PIPELINE SCAN ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        // UI Loading State
        submitBtn.disabled = true;
        submitBtn.textContent = 'Checking...';
        verdictPill.textContent = 'Analyzing...';
        verdictPill.className = 'text-xs font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200';
        detailsBox.classList.add('hidden');

        // Render Active Pipeline Animation State
        const langName = LANG_LABELS[currentLang] || currentLang;
        pipelineSteps.innerHTML = `
            <div class="flex items-start space-x-3 text-indigo-600 animate-pulse">
                <span class="text-lg">⏳</span>
                <div>
                    <p class="font-semibold text-slate-800">Running Hybrid Pipeline...</p>
                    <p class="text-xs text-slate-500">Executing deterministic rules and querying Groq AI (${langName} reasoning)</p>
                </div>
            </div>
        `;

        try {
            const response = await httpsFetch(message, currentLang);
            const data = await response.json();

            // Determine Verdict & Styling
            const isScam = data.verdict === 'scam' || data.is_scam === true;
            verdictPill.textContent = isScam ? '⚠️ SCAM DETECTED' : '✅ MESSAGE SAFE';
            verdictPill.className = isScam
                ? 'text-xs font-bold px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200'
                : 'text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200';

            // Populate Pipeline Success View
            pipelineSteps.innerHTML = `
                <div class="flex items-start space-x-3 text-emerald-600">
                    <span class="text-lg">✅</span>
                    <div>
                        <p class="font-semibold text-slate-800">Pipeline Completed (${langName})</p>
                        <p class="text-xs text-slate-500">Cleaned -> Rule Checked -> AI Evaluated (${langName}) -> Verdict Merged</p>
                    </div>
                </div>
            `;

            // Populate Details Box
            detailsBox.classList.remove('hidden');
            reasonText.textContent = data.reason || 'Hybrid engine completed evaluation.';

            // Score & Flags Evaluation Logic
            const rawScore = data.rules && data.rules.score !== undefined ? data.rules.score : (data.score || 0);
            const flags = (data.rules && data.rules.flags) || data.rules_triggered || [];

            if (isScam) {
                // Display Risk Score & Triggered Red Flag Badges for Scams
                scoreBadge.textContent = `Risk Score: ${rawScore}/100`;
                scoreBadge.className = 'text-xs font-mono font-bold px-2.5 py-1 rounded bg-red-100 text-red-700 border border-red-200';

                if (flags.length > 0) {
                    flagsContainer.innerHTML = flags.map(flag => {
                        const label = flag.label || flag;
                        const weight = flag.weight ? ` (+${flag.weight}pts)` : '';
                        return `<div class="text-xs bg-slate-100 border border-slate-200 text-slate-700 p-2 rounded-lg flex justify-between items-center">
                            <span>🛡️ ${escapeHtml(label)}</span>
                            <span class="font-mono text-slate-500">${weight}</span>
                        </div>`;
                    }).join('');
                } else {
                    flagsContainer.innerHTML = `<p class="text-xs text-slate-400 italic">No specific rule flags triggered.</p>`;
                }
            } else {
                // If message is SAFE, override false-positive rule flags
                scoreBadge.textContent = `Risk Score: 0/100`;
                scoreBadge.className = 'text-xs font-mono font-bold px-2.5 py-1 rounded bg-emerald-100 text-emerald-700 border border-emerald-200';
                flagsContainer.innerHTML = `<p class="text-xs text-emerald-700 font-medium">✅ No active threat signals detected.</p>`;
            }

        } catch (err) {
            pipelineSteps.innerHTML = `
                <div class="flex items-start space-x-3 text-red-600">
                    <span class="text-lg">❌</span>
                    <div>
                        <p class="font-semibold text-slate-800">Connection Error</p>
                        <p class="text-xs text-red-500">Could not reach backend API server.</p>
                    </div>
                </div>
            `;
            verdictPill.textContent = 'Error';
            verdictPill.className = 'text-xs font-bold px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Check message';
        }
    });

    async function httpsFetch(message, lang) {
        return await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, language: lang })
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});