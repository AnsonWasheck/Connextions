// Vertex - Professional Network Client Script
// ────────────────────────────────────────────────────────────────

lucide.createIcons();

// ── Theme handling ───────────────────────────────────────────────
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme') || 'light';
    const newTheme = current === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icons safely (they may not exist on login/register pages)
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon  = document.getElementById('theme-icon-dark');

    if (lightIcon && darkIcon) {
        lightIcon.style.display = newTheme === 'dark' ? 'none'  : 'block';
        darkIcon.style.display  = newTheme === 'dark' ? 'block' : 'none';
    }

    lucide.createIcons();
}

function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);

    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon  = document.getElementById('theme-icon-dark');

    if (lightIcon && darkIcon) {
        lightIcon.style.display = saved === 'dark' ? 'none'  : 'block';
        darkIcon.style.display  = saved === 'dark' ? 'block' : 'none';
    }

    lucide.createIcons();
}

// ── Filter population ─────────────────────────────────────────────
function populateFilters() {
    const rows = document.querySelectorAll('.connection-row');
    const industries = new Set();

    rows.forEach(row => {
        const industry = row.dataset.industry;
        if (industry && industry !== 'None') {
            industries.add(industry);
        }
    });

    const industryFilter = document.getElementById('industry-filter');
    if (industryFilter) {
        industries.forEach(industry => {
            const option = document.createElement('option');
            option.value = industry;
            option.textContent = industry;
            industryFilter.appendChild(option);
        });
    }
}

// ── Connection expand/collapse ────────────────────────────────────
function toggleExpand(row) {
    const details = row.querySelector('.connection-details');
    const icon = row.querySelector('.expand-icon');
    const isExpanded = details.classList.contains('show');

    // Close all others
    document.querySelectorAll('.connection-details.show').forEach(d => {
        d.classList.remove('show');
        d.closest('.connection-row').classList.remove('expanded');
    });
    document.querySelectorAll('.expand-icon.rotated').forEach(i => {
        i.classList.remove('rotated');
    });

    if (!isExpanded) {
        details.classList.add('show');
        row.classList.add('expanded');
        icon.classList.add('rotated');
    }

    lucide.createIcons();
}

// ── Add connection modal ──────────────────────────────────────────
function openModal() {
    document.getElementById('add-modal').classList.add('show');
    lucide.createIcons();
}

function closeModal() {
    document.getElementById('add-modal').classList.remove('show');
}

// ── Quick AI queries ──────────────────────────────────────────────
function quickQuery(query) {
    document.getElementById('ai-query').value = query;
    runAISearch();
}

// ── AI search / chat ──────────────────────────────────────────────
async function runAISearch() {
    const input   = document.getElementById('ai-query');
    const chat    = document.getElementById('ai-chat');
    const sendBtn = document.getElementById('send-btn');
    const query   = input.value.trim();

    if (!query) return;

    // User message
    const userMsg = document.createElement('div');
    userMsg.className = 'user-msg';
    userMsg.textContent = query;
    chat.appendChild(userMsg);
    input.value = "";

    sendBtn.disabled = true;

    // Typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    chat.appendChild(typingDiv);
    chat.scrollTop = chat.scrollHeight;

    try {
        const res = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, context: "Vertex General Session" })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        typingDiv.remove();

        const aiMsg = document.createElement('div');
        aiMsg.className = 'ai-msg';

        let text = data.answer || "No response received.";
        text = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        text = '<p>' + text + '</p>';
        text = text.replace('<p></p>', '');

        aiMsg.innerHTML = text;
        chat.appendChild(aiMsg);

    } catch (error) {
        console.error(error);
        typingDiv.remove();
        const errorMsg = document.createElement('div');
        errorMsg.className = 'ai-msg';
        errorMsg.textContent = 'Error connecting to AI assistant.';
        chat.appendChild(errorMsg);
    }

    sendBtn.disabled = false;
    chat.scrollTop = chat.scrollHeight;
    lucide.createIcons();
}

// ── Sorting ───────────────────────────────────────────────────────
function sortConnections() {
    const sortValue = document.getElementById('sort-filter').value;
    const container = document.getElementById('connections-list');
    const rows = Array.from(container.querySelectorAll('.connection-row'));

    rows.sort((a, b) => {
        switch (sortValue) {
            case 'rating-high':
                return parseInt(b.dataset.rating) - parseInt(a.dataset.rating);
            case 'rating-low':
                return parseInt(a.dataset.rating) - parseInt(b.dataset.rating);
            case 'name':
                return a.dataset.name.localeCompare(b.dataset.name);
            case 'last-contact':
                return parseInt(a.dataset.contact) - parseInt(b.dataset.contact);
            case 'recent':
            default:
                return 0;
        }
    });

    rows.forEach(row => container.appendChild(row));
    lucide.createIcons();
}

// ── Filtering ─────────────────────────────────────────────────────
function filterConnections() {
    const industryValue     = document.getElementById('industry-filter').value;
    const momentumValue     = document.getElementById('momentum-filter').value;
    const relationshipValue = document.getElementById('relationship-filter').value;

    const rows = document.querySelectorAll('.connection-row');

    rows.forEach(row => {
        const industry     = row.dataset.industry;
        const momentum     = row.dataset.momentum;
        const relationship = row.dataset.relationship;

        const industryMatch     = industryValue === 'all' || industry === industryValue;
        const momentumMatch     = momentumValue === 'all' || momentum === momentumValue;
        const relationshipMatch = relationshipValue === 'all' || relationship === relationshipValue;

        row.style.display = (industryMatch && momentumMatch && relationshipMatch) ? '' : 'none';
    });
}

// ── Add new connection ────────────────────────────────────────────
async function submitNewConnection() {
    const nameEl = document.getElementById('f-full_name');
    if (!nameEl.value.trim()) {
        nameEl.style.borderColor = 'var(--danger)';
        nameEl.focus();
        return;
    }

    const fields = [
        'full_name', 'contact_info', 'job_title', 'company',
        'industry', 'sector', 'skills_experience', 'ai_rating',
        'rating_momentum', 'relationship_status', 'days_since_contact',
        'mutual_connections', 'key_accomplishments', 'personal_notes', 'ai_summary'
    ];

    const formData = new FormData();
    fields.forEach(name => {
        formData.append(name, document.getElementById('f-' + name).value);
    });

    const btn = document.querySelector('#add-form .add-btn');
    btn.disabled = true;
    btn.style.opacity = '0.6';

    try {
        const res = await fetch('/add', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Server responded ' + res.status);

        window.location.reload();

    } catch (err) {
        console.error('Add connection failed:', err);
        btn.disabled = false;
        btn.style.opacity = '1';
        alert('Something went wrong while saving. Check the console for details.');
    }
}

// ─── MODAL & TABS ───────────────────────────────────────────────────

function openModal() {
    document.getElementById('add-modal').style.display = 'flex';
    switchTab('voice'); // you can change to 'manual' if preferred
}

function closeModal() {
    document.getElementById('add-modal').style.display = 'none';
    resetVoiceUI();
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');

    if (tab === 'manual') {
        document.getElementById('tab-manual').style.display = 'block';
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
    } else {
        document.getElementById('tab-voice').style.display = 'block';
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
    }
}

// ─── VOICE RECORDING ────────────────────────────────────────────────

let mediaRecorder = null;
let audioChunks = [];

function resetVoiceUI() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    audioChunks = [];
    document.getElementById('voice-status').textContent = "Click \"Start\" and describe the person you just met...";
    document.getElementById('voice-result').textContent = "";
    document.getElementById('btn-start-record').style.display = 'inline-block';
    document.getElementById('btn-stop-record').style.display = 'none';
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            const reader = new FileReader();

            reader.onloadend = async function() {
                const base64data = reader.result;

                document.getElementById('voice-status').textContent = "Processing audio...";
                document.getElementById('btn-start-record').style.display = 'none';
                document.getElementById('btn-stop-record').style.display = 'none';

                try {
                    const response = await fetch('/api/process-audio', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ audio: base64data })
                    });

                    const result = await response.json();

                    if (!response.ok || !result.success) {
                        throw new Error(result.error || 'Failed to process audio');
                    }

                    const name = result.data.full_name || 'New contact';
                    const rating = result.data.ai_rating;
                    const summary = result.data.ai_summary || '';

                    document.getElementById('voice-result').innerHTML =
                        `Added <strong>${name}</strong><br>` +
                        `Rating: ${rating}/10<br>` +
                        `<small>${summary.substring(0, 120)}${summary.length > 120 ? '...' : ''}</small>`;

                    // Auto refresh after success
                    setTimeout(() => location.reload(), 2200);

                } catch (err) {
                    document.getElementById('voice-result').textContent = "Error: " + err.message;
                    document.getElementById('voice-status').textContent = "Failed — try again?";
                }
            };

            reader.readAsDataURL(blob);
        };

        mediaRecorder.start();
        document.getElementById('voice-status').textContent = "Recording... Speak clearly!";
        document.getElementById('btn-start-record').style.display = 'none';
        document.getElementById('btn-stop-record').style.display = 'inline-block';

    } catch (err) {
        alert("Cannot access microphone.\n" + err.message);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
}

// ── Open Profile in New Tab ───────────────────────────────────────
function openProfile(personId) {
    // Open the profile page in a new tab
    window.open(`/profile/${personId}`, '_blank');
}

// ─── EVENT LISTENERS ────────────────────────────────────────────────

document.getElementById('btn-start-record')?.addEventListener('click', startRecording);
document.getElementById('btn-stop-record')?.addEventListener('click', stopRecording);

// Your existing functions: submitNewConnection(), toggleExpand(), etc. remain below...

// ── Initialize everything when DOM is ready ───────────────────────
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    populateFilters();
    lucide.createIcons();
});