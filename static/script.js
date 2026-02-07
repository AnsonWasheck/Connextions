// ══════════════════════════════════════════════════════════════════
// CONNEXTIONS - Network Management App (ENHANCED AI CHATBOT)
// Combines original functionality with enhanced AI features
// ══════════════════════════════════════════════════════════════════

// Initialize Lucide icons and theme on load
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initTheme();
    populateFilters();
    initAIChatFeatures();
});

// ─── THEME MANAGEMENT ─────────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    
    if (lightIcon && darkIcon) {
        lightIcon.style.display = saved === 'dark' ? 'none' : 'block';
        darkIcon.style.display = saved === 'dark' ? 'block' : 'none';
    }
    
    lucide.createIcons();
}

function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme') || 'light';
    const newTheme = current === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    
    if (lightIcon && darkIcon) {
        lightIcon.style.display = newTheme === 'dark' ? 'none' : 'block';
        darkIcon.style.display = newTheme === 'dark' ? 'block' : 'none';
    }
    
    lucide.createIcons();
}

// ─── FILTER MANAGEMENT ─────────────────────────────────────────────
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

function filterConnections() {
    const industryValue = document.getElementById('industry-filter').value;
    const momentumValue = document.getElementById('momentum-filter').value;
    const relationshipValue = document.getElementById('relationship-filter').value;
    
    const rows = document.querySelectorAll('.connection-row');
    
    rows.forEach(row => {
        const industry = row.dataset.industry;
        const momentum = row.dataset.momentum;
        const relationship = row.dataset.relationship;
        
        const industryMatch = industryValue === 'all' || industry === industryValue;
        const momentumMatch = momentumValue === 'all' || momentum === momentumValue;
        const relationshipMatch = relationshipValue === 'all' || relationship === relationshipValue;
        
        row.style.display = (industryMatch && momentumMatch && relationshipMatch) ? '' : 'none';
    });
}

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

// ─── CONNECTION EXPANSION ─────────────────────────────────────────
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

function openProfile(personId) {
    // Open profile in new tab
    window.open(`/profile/${personId}`, '_blank');
}

// ─── MODAL MANAGEMENT ─────────────────────────────────────────────
function openModal() {
    document.getElementById('add-modal').style.display = 'flex';
    switchTab('voice'); // Default to voice tab
    lucide.createIcons();
}

function closeModal() {
    document.getElementById('add-modal').style.display = 'none';
    resetVoiceUI();
    resetManualForm();
}

function switchTab(tab) {
    // Remove active from all tabs
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    // Hide all content
    document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
    
    if (tab === 'manual') {
        document.getElementById('tab-manual').style.display = 'block';
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
    } else {
        document.getElementById('tab-voice').style.display = 'block';
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
    }
    
    lucide.createIcons();
}

function resetManualForm() {
    const form = document.getElementById('add-form');
    if (form) {
        form.querySelectorAll('input, textarea, select').forEach(el => {
            if (el.type === 'number') {
                el.value = el.id === 'f-ai_rating' ? 5 : 0;
            } else {
                el.value = '';
            }
        });
    }
}

// ─── MANUAL CONNECTION SUBMIT ─────────────────────────────────────
async function submitNewConnection() {
    const nameEl = document.getElementById('f-full_name');
    if (!nameEl || !nameEl.value.trim()) {
        if (nameEl) {
            nameEl.style.borderColor = 'var(--danger, #ef4444)';
            nameEl.focus();
        }
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
        const el = document.getElementById('f-' + name);
        if (el) {
            formData.append(name, el.value || '');
        }
    });
    
    const btn = document.querySelector('#add-form .add-btn');
    if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.6';
    }
    
    try {
        const res = await fetch('/add', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) throw new Error('Server responded ' + res.status);
        
        window.location.reload();
        
    } catch (err) {
        console.error('Add connection failed:', err);
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = '1';
        }
        alert('Something went wrong while saving. Check the console for details.');
    }
}

// ─── VOICE RECORDING ────────────────────────────────────────────────
let mediaRecorder = null;
let audioChunks = [];

function resetVoiceUI() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    audioChunks = [];
    
    const statusEl = document.getElementById('voice-status');
    const resultEl = document.getElementById('voice-result');
    const startBtn = document.getElementById('btn-start-record');
    const stopBtn = document.getElementById('btn-stop-record');
    
    if (statusEl) statusEl.textContent = 'Click "Start" and describe the person you just met...';
    if (resultEl) resultEl.textContent = '';
    if (startBtn) startBtn.style.display = 'inline-block';
    if (stopBtn) stopBtn.style.display = 'none';
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };
        
        mediaRecorder.onstop = processRecording;
        
        mediaRecorder.start();
        
        const statusEl = document.getElementById('voice-status');
        const startBtn = document.getElementById('btn-start-record');
        const stopBtn = document.getElementById('btn-stop-record');
        
        if (statusEl) statusEl.textContent = '🎙️ Recording... Speak clearly!';
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'inline-block';
        
        lucide.createIcons();
        
    } catch (err) {
        alert('Cannot access microphone.\n' + err.message);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

async function processRecording() {
    const blob = new Blob(audioChunks, { type: 'audio/webm' });
    const reader = new FileReader();
    
    reader.onloadend = async function() {
        const base64data = reader.result;
        
        const statusEl = document.getElementById('voice-status');
        const resultEl = document.getElementById('voice-result');
        const startBtn = document.getElementById('btn-start-record');
        const stopBtn = document.getElementById('btn-stop-record');
        
        if (statusEl) statusEl.textContent = '⏳ Processing audio...';
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'none';
        
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
            
            if (statusEl) statusEl.textContent = '✅ Connection added successfully!';
            if (resultEl) {
                resultEl.innerHTML =
                    `Added <strong>${name}</strong><br>` +
                    `Rating: ${rating}/10<br>` +
                    `<small>${summary.substring(0, 120)}${summary.length > 120 ? '...' : ''}</small>`;
            }
            
            // Auto refresh after success
            setTimeout(() => location.reload(), 2200);
            
        } catch (err) {
            if (resultEl) resultEl.textContent = 'Error: ' + err.message;
            if (statusEl) statusEl.textContent = 'Failed — try again?';
            if (startBtn) startBtn.style.display = 'inline-block';
        }
    };
    
    reader.readAsDataURL(blob);
}

// Attach event listeners for voice recording buttons
document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('btn-start-record');
    const stopBtn = document.getElementById('btn-stop-record');
    
    if (startBtn) startBtn.addEventListener('click', startRecording);
    if (stopBtn) stopBtn.addEventListener('click', stopRecording);
});

// ─── ENHANCED AI CHAT FEATURES ─────────────────────────────────────

/**
 * Initialize AI chat features
 */
function initAIChatFeatures() {
    initAutoResizeTextarea();
    
    // Add keyboard shortcuts
    const input = document.getElementById('ai-query');
    if (input) {
        // Enter to send (Shift+Enter for new line)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                runAISearch();
            }
            
            // Escape to clear input
            if (e.key === 'Escape') {
                input.value = '';
                input.style.height = 'auto';
                input.blur();
            }
        });
        
        // Focus input when user presses '/'
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement !== input) {
                e.preventDefault();
                input.focus();
            }
        });
    }
}

/**
 * Auto-resize textarea as user types
 */
function initAutoResizeTextarea() {
    const textarea = document.getElementById('ai-query');
    if (!textarea) return;
    
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

/**
 * Enhanced quick query with typing animation
 */
function quickQuery(query) {
    const input = document.getElementById('ai-query');
    if (!input) return;
    
    // Clear and focus
    input.value = '';
    input.style.height = 'auto';
    input.focus();
    
    // Type out the query with animation
    let i = 0;
    const typeInterval = setInterval(() => {
        if (i < query.length) {
            input.value += query[i];
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            i++;
        } else {
            clearInterval(typeInterval);
            // Auto-trigger search after typing
            setTimeout(() => runAISearch(), 300);
        }
    }, 30);
}

/**
 * Enhanced AI search with better UX
 */
async function runAISearch() {
    const input = document.getElementById('ai-query');
    const chat = document.getElementById('ai-chat');
    const sendBtn = document.getElementById('send-btn');
    
    if (!input || !chat) return;
    
    const query = input.value.trim();
    if (!query) {
        // Shake animation if empty
        input.style.animation = 'shake 0.3s';
        setTimeout(() => input.style.animation = '', 300);
        return;
    }
    
    // Add user message
    addUserMessage(query);
    input.value = '';
    input.style.height = 'auto';
    
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.style.opacity = '0.5';
    }
    
    // Add typing indicator
    const typingDiv = addTypingIndicator();
    
    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        // Remove typing indicator
        removeTypingIndicator(typingDiv);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Search failed');
        }
        
        const data = await response.json();
        
        // Display the enhanced AI response
        displayAIResponse(data);
        
    } catch (error) {
        console.error('Search error:', error);
        removeTypingIndicator(typingDiv);
        
        // Show friendly error message
        addErrorMessage(error.message || 'Unable to process your query. Please try again.');
    }
    
    if (sendBtn) {
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
    }
    
    chat.scrollTop = chat.scrollHeight;
    lucide.createIcons();
}

/**
 * Add user message to chat
 */
function addUserMessage(text) {
    const chat = document.getElementById('ai-chat');
    if (!chat) return;
    
    const userMsg = document.createElement('div');
    userMsg.className = 'user-msg';
    userMsg.textContent = text;
    chat.appendChild(userMsg);
    chat.scrollTop = chat.scrollHeight;
}

/**
 * Add typing indicator
 */
function addTypingIndicator() {
    const chat = document.getElementById('ai-chat');
    if (!chat) return null;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    chat.appendChild(typingDiv);
    chat.scrollTop = chat.scrollHeight;
    
    return typingDiv;
}

/**
 * Remove typing indicator with animation
 */
function removeTypingIndicator(element) {
    if (!element || !element.parentNode) return;
    element.style.opacity = '0';
    element.style.transform = 'scale(0.9)';
    element.style.transition = 'all 0.2s ease';
    setTimeout(() => element.remove(), 200);
}

/**
 * Add error message
 */
function addErrorMessage(message) {
    const chat = document.getElementById('ai-chat');
    if (!chat) return;
    
    const errorMsg = document.createElement('div');
    errorMsg.className = 'ai-msg';
    errorMsg.innerHTML = `
        <div style="display: flex; align-items: start; gap: 10px;">
            <div style="color: var(--danger); margin-top: 2px;">⚠️</div>
            <div>
                <strong style="color: var(--danger);">Error</strong><br>
                <span style="color: var(--text-secondary);">${escapeHtml(message)}</span>
            </div>
        </div>
    `;
    chat.appendChild(errorMsg);
    chat.scrollTop = chat.scrollHeight;
}

/**
 * Display enhanced AI response
 */
function displayAIResponse(data) {
    const chat = document.getElementById('ai-chat');
    if (!chat) return;
    
    const content = data.content || {};
    
    // Build formatted message
    let message = `<div class="ai-response">`;
    
    // Title
    if (content.title) {
        message += `<div class="ai-response-title">${escapeHtml(content.title)}</div>`;
    }
    
    // Summary
    if (content.summary) {
        message += `<div class="ai-response-summary">${escapeHtml(content.summary)}</div>`;
    }
    
    // Main body with markdown-style formatting
    if (content.body) {
        const formattedBody = formatMessageBody(content.body);
        message += `<div class="ai-response-body">${formattedBody}</div>`;
    }
    
    // Insights
    if (content.insights && content.insights.length > 0) {
        message += `<div class="ai-insights">`;
        message += `<strong>💡 Key Insights</strong>`;
        content.insights.forEach(insight => {
            message += `<div style="margin-top: 6px;">• ${escapeHtml(insight)}</div>`;
        });
        message += `</div>`;
    }
    
    // Results list
    if (data.results && data.results.length > 0) {
        message += `<div class="ai-results">`;
        data.results.forEach((result) => {
            const conn = result.connection;
            message += createResultCard(conn, result.score);
        });
        message += `</div>`;
    }
    
    // Metadata
    if (data.metadata) {
        const count = data.metadata.result_count || 0;
        const time = data.metadata.processing_time || 0;
        message += `
            <div class="ai-metadata">
                Found ${count} result${count !== 1 ? 's' : ''} in ${time}s
            </div>
        `;
    }
    
    message += `</div>`;
    
    const aiMsg = document.createElement('div');
    aiMsg.className = 'ai-msg';
    aiMsg.innerHTML = message;
    chat.appendChild(aiMsg);
    
    chat.scrollTop = chat.scrollHeight;
}

/**
 * Create a result card
 */
function createResultCard(conn, score) {
    return `
        <div class="ai-result-item" onclick="openProfile('${conn.id}')">
            <div class="ai-result-content">
                <div class="ai-result-header">
                    <strong>${escapeHtml(conn.name || 'Unknown')}</strong>
                    <span class="ai-result-score">${score || 'N/A'}</span>
                </div>
                <div class="ai-result-meta">
                    ${escapeHtml(conn.title || 'No title')} ${conn.company ? 'at ' + escapeHtml(conn.company) : ''}
                </div>
            </div>
            <div class="ai-result-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>
    `;
}

/**
 * Format message body with markdown-like syntax
 */
function formatMessageBody(text) {
    return escapeHtml(text)
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── SEARCH BAR (SIMPLE TEXT FILTER) ──────────────────────────────
const searchInput = document.querySelector('.search-input');
if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        document.querySelectorAll('.connection-row').forEach(row => {
            const name = row.dataset.name ? row.dataset.name.toLowerCase() : '';
            const text = row.textContent.toLowerCase();
            row.style.display = (name.includes(searchTerm) || text.includes(searchTerm)) ? '' : 'none';
        });
    });
}

// ─── KEYBOARD SHORTCUTS ───────────────────────────────────────────
document.addEventListener('keydown', function(e) {
    // Escape to close modal
    if (e.key === 'Escape') {
        const modal = document.getElementById('add-modal');
        if (modal && modal.style.display === 'flex') {
            closeModal();
        }
    }
});

// ─── MODAL OUTSIDE CLICK ──────────────────────────────────────────
window.addEventListener('click', function(event) {
    const modal = document.getElementById('add-modal');
    if (event.target === modal) {
        closeModal();
    }
});

// ─── ADD SHAKE ANIMATION ──────────────────────────────────────────
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);