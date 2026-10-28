document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('scan-form');
    const submitBtn = document.getElementById('submit-btn');
    const placeholderContainer = document.getElementById('result-container');
    const threatCard = document.getElementById('threat-card');

    const verdictBadge = document.getElementById('verdict-badge');
    const confidenceScore = document.getElementById('confidence-score');
    const analysisReason = document.getElementById('analysis-reason');
    const rulesSection = document.getElementById('rules-section');
    const rulesList = document.getElementById('rules-list');
    const quotesSection = document.getElementById('quotes-section');
    const quotesList = document.getElementById('quotes-list');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        if (!message) return;

        // Set Loading UI
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Scanning...</span>`;
        placeholderContainer.classList.remove('hidden');
        placeholderContainer.innerHTML = `
            <div class="text-2xl mb-2 scanning-loader">⏳</div>
            <p class="text-sm text-slate-400">Running deterministic checks and LLM analysis...</p>
        `;
        threatCard.classList.add('hidden');

        try {
            const response = await fetch('https://scam-check-jriu.onrender.com/api/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, language: 'en' })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();

            // Hide Loading State & Show Result Card
            placeholderContainer.classList.add('hidden');
            threatCard.classList.remove('hidden');

            // Verdict Styling
            const isScam = data.is_scam;
            verdictBadge.textContent = isScam ? '⚠️ High Risk Scam Detected' : '✅ Message Appears Safe';
            verdictBadge.className = isScam
                ? 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-red-500/10 text-red-400 border border-red-500/20'
                : 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';

            confidenceScore.textContent = `${Math.round((data.confidence || 0) * 100)}%`;
            analysisReason.textContent = data.reason || 'No detailed breakdown provided.';

            // Render Triggered Rules
            if (data.rules_triggered && data.rules_triggered.length > 0) {
                rulesSection.classList.remove('hidden');
                rulesList.innerHTML = data.rules_triggered.map(rule =>
                    `<span class="bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs px-2.5 py-1 rounded-lg font-mono">${escapeHtml(rule)}</span>`
                ).join('');
            } else {
                rulesSection.classList.add('hidden');
            }

            // Render Flagged Phrases
            if (data.quotes && data.quotes.length > 0) {
                quotesSection.classList.remove('hidden');
                quotesList.innerHTML = data.quotes.map(q =>
                    `<div class="text-xs font-mono bg-red-950/30 text-red-300 border border-red-900/50 p-2 rounded-lg">"${escapeHtml(q)}"</div>`
                ).join('');
            } else {
                quotesSection.classList.add('hidden');
            }

        } catch (err) {
            placeholderContainer.innerHTML = `
                <div class="text-2xl mb-2 text-red-400">⚠️</div>
                <p class="text-sm text-red-400">Error: Could not evaluate message. Make sure the API service is active.</p>
            `;
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<span>Scan Threat</span>`;
        }
    });

    // Helper to prevent HTML injection in user inputs
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});