document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('scan-form');
    const messageInput = document.getElementById('message-input');
    const submitBtn = document.getElementById('submit-btn');
    const verdictPill = document.getElementById('verdict-pill');
    const pipelineSteps = document.getElementById('pipeline-steps');
    const detailsBox = document.getElementById('details-box');
    const scoreBadge = document.getElementById('score-badge');
    const flagsContainer = document.getElementById('flags-container');
    const reasonText = document.getElementById('reason-text');

    let currentLang = 'en';

    // Language switcher buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.lang-btn').forEach(b => {
                b.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
                b.classList.add('text-slate-500');
            });
            e.target.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
            e.target.classList.remove('text-slate-500');
            currentLang = e.target.getAttribute('data-lang');
        });
    });

    // Sample buttons functionality
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            messageInput.value = e.target.getAttribute('data-msg');
        });
    });

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
        pipelineSteps.innerHTML = `
            <div class="flex items-start space-x-3 text-indigo-600 animate-pulse">
                <span class="text-lg">⏳</span>
                <div>
                    <p class="font-semibold text-slate-800">Running Hybrid Pipeline...</p>
                    <p class="text-xs text-slate-500">Executing rule engine and querying Groq LLM inference</p>
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
                        <p class="font-semibold text-slate-800">Pipeline Completed Successfully</p>
                        <p class="text-xs text-slate-500">Cleaned -> Rule Checked -> AI Evaluated -> Verdict Merged</p>
                    </div>
                </div>
            `;

            // Populate Details Box
            detailsBox.classList.remove('hidden');
            reasonText.textContent = data.reason || 'Hybrid engine completed evaluation.';

            // Score & Flags
            const score = data.rules && data.rules.score !== undefined ? data.rules.score : (data.score || 0);
            scoreBadge.textContent = `Risk Score: ${score}/100`;
            scoreBadge.className = score > 50
                ? 'text-xs font-mono font-bold px-2.5 py-1 rounded bg-red-100 text-red-700 border border-red-200'
                : 'text-xs font-mono font-bold px-2.5 py-1 rounded bg-emerald-100 text-emerald-700 border border-emerald-200';

            const flags = (data.rules && data.rules.flags) || data.rules_triggered || [];
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
                flagsContainer.innerHTML = `<p class="text-xs text-slate-400 italic">No red flag rules triggered.</p>`;
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