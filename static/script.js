// ══════════════════════════════════════════════════════════════════
// CONNEXTIONS - Enhanced Frontend with Smart AI Display
// v3.0 - Cleaner cards, context-aware display, better UX
// ══════════════════════════════════════════════════════════════════

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initTheme();
    populateFilters();
    initAIChatFeatures();
    initEnhancedCardAnimations();
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
    window.open(`/profile/${personId}`, '_blank');
}

// ─── MODAL MANAGEMENT ─────────────────────────────────────────────
function openModal() {
    document.getElementById('add-modal').style.display = 'flex';
    switchTab('voice');
    lucide.createIcons();
}

function closeModal() {
    document.getElementById('add-modal').style.display = 'none';
    resetVoiceUI();
    resetManualForm();
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
            
            setTimeout(() => location.reload(), 2200);
            
        } catch (err) {
            if (resultEl) resultEl.textContent = 'Error: ' + err.message;
            if (statusEl) statusEl.textContent = 'Failed — try again?';
            if (startBtn) startBtn.style.display = 'inline-block';
        }
    };
    
    reader.readAsDataURL(blob);
}

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('btn-start-record');
    const stopBtn = document.getElementById('btn-stop-record');
    
    if (startBtn) startBtn.addEventListener('click', startRecording);
    if (stopBtn) stopBtn.addEventListener('click', stopRecording);
});

// ═══════════════════════════════════════════════════════════════════
// ENHANCED AI CHAT FEATURES - v3.0
// ═══════════════════════════════════════════════════════════════════

/**
 * Initialize AI chat features
 */
function initAIChatFeatures() {
    initAutoResizeTextarea();
    
    const input = document.getElementById('ai-query');
    if (input) {
        // Enter to send (Shift+Enter for new line)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                runAISearch();
            }
            
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
 * Auto-resize textarea
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
 * Quick query with typing animation
 */
function quickQuery(query) {
    const input = document.getElementById('ai-query');
    if (!input) return;
    
    input.value = '';
    input.style.height = 'auto';
    input.focus();
    
    let i = 0;
    const typeInterval = setInterval(() => {
        if (i < query.length) {
            input.value += query[i];
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            i++;
        } else {
            clearInterval(typeInterval);
            setTimeout(() => runAISearch(), 300);
        }
    }, 30);
}

/**
 * Enhanced AI search with smart display logic
 */
async function runAISearch() {
    const input = document.getElementById('ai-query');
    const chat = document.getElementById('ai-chat');
    const sendBtn = document.getElementById('send-btn');
    
    if (!input || !chat) return;
    
    const query = input.value.trim();
    if (!query) {
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
    
    const typingDiv = addTypingIndicator();
    
    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        removeTypingIndicator(typingDiv);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Search failed');
        }
        
        const data = await response.json();
        
        // SMART DISPLAY: Determine how to show results
        displaySmartAIResponse(data, query);
        
    } catch (error) {
        console.error('Search error:', error);
        removeTypingIndicator(typingDiv);
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
 * Smart AI Response Display
 * Context-aware: shows 1 card for profiles, 3 for searches, none for insights
 */
function displaySmartAIResponse(data, originalQuery) {
    const chat = document.getElementById('ai-chat');
    if (!chat) return;
    
    const content = data.content || {};
    const intent = data.intent || 'general_search';
    const results = data.results || [];
    
    // Determine how many cards to show based on intent
    let cardCount = 0;
    let showFullCards = false;
    
    if (intent === 'profile_lookup' && results.length === 1) {
        // Single person profile: show ONE detailed card
        cardCount = 1;
        showFullCards = true;
    } else if (intent === 'network_analysis') {
        // Network insights: NO cards, just stats
        cardCount = 0;
    } else if (results.length > 0) {
        // Everything else: top 3 compact cards
        cardCount = Math.min(3, results.length);
        showFullCards = false;
    }
    
    // Build message
    let message = `<div class="ai-response">`;
    
    // Title
    if (content.title) {
        message += `<div class="ai-response-title">${escapeHtml(content.title)}</div>`;
    }
    
    // Summary (only if not redundant)
    if (content.summary && content.summary !== content.title) {
        message += `<div class="ai-response-summary">${escapeHtml(content.summary)}</div>`;
    }
    
    // Main body with markdown formatting
    if (content.body) {
        const formattedBody = formatMessageBody(content.body);
        message += `<div class="ai-response-body">${formattedBody}</div>`;
    }
    
    // Context insights (if present)
    if (content.context && content.context.length > 0) {
        message += `<div class="ai-context">`;
        content.context.forEach(ctx => {
            message += `<span class="context-badge">${escapeHtml(ctx)}</span>`;
        });
        message += `</div>`;
    }
    
    // Next steps (if present)
    if (content.next_steps && content.next_steps.length > 0) {
        message += `<div class="ai-next-steps">`;
        message += `<div class="next-steps-label">💡 Suggested actions:</div>`;
        content.next_steps.forEach(step => {
            message += `<div class="next-step-item">• ${escapeHtml(step)}</div>`;
        });
        message += `</div>`;
    }
    
    // Smart card display
    if (cardCount > 0) {
        message += `<div class="ai-results">`;
        
        for (let i = 0; i < cardCount; i++) {
            const result = results[i];
            if (showFullCards) {
                message += createDetailedCard(result);
            } else {
                message += createCompactCard(result);
            }
        }
        
        message += `</div>`;
        
        // "See more" hint if there are additional results
        if (results.length > cardCount) {
            const remaining = results.length - cardCount;
            message += `<div class="see-more-hint">+${remaining} more connection${remaining !== 1 ? 's' : ''} found</div>`;
        }
    }
    
    // Metadata (subtle)
    if (data.meta) {
        const count = data.meta.count || 0;
        const time = data.meta.time || 0;
        message += `
            <div class="ai-metadata">
                ${count} result${count !== 1 ? 's' : ''} • ${time}s
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
 * Create detailed card (for single profile lookups)
 */
function createDetailedCard(result) {
    const conn = result.connection;
    const angle = result.angle || result.why || '';
    const traits = conn.unique_traits || [];
    
    return `
        <div class="ai-card ai-card-detailed" onclick="openProfile('${conn.id}')">
            <div class="ai-card-header">
                <div class="ai-card-name">${escapeHtml(conn.name || 'Unknown')}</div>
                ${conn.relationship !== 'Professional' ? 
                    `<span class="relationship-badge">${escapeHtml(conn.relationship)}</span>` : 
                    ''
                }
            </div>
            
            <div class="ai-card-role">
                ${escapeHtml(conn.title || 'No title')}
                ${conn.company ? ` at ${escapeHtml(conn.company)}` : ''}
            </div>
            
            ${angle ? `<div class="ai-card-angle">→ ${escapeHtml(angle)}</div>` : ''}
            
            ${traits.length > 0 ? `
                <div class="ai-card-traits">
                    <div class="traits-label">What makes them special:</div>
                    ${traits.slice(0, 2).map(trait => 
                        `<div class="trait-item">• ${escapeHtml(trait)}</div>`
                    ).join('')}
                </div>
            ` : ''}
            
            <div class="ai-card-footer">
                <span class="footer-item">${conn.last_contact || 'Unknown last contact'}</span>
                ${conn.industry && conn.industry !== 'N/A' ? 
                    `<span class="footer-divider">•</span>
                     <span class="footer-item">${escapeHtml(conn.industry)}</span>` : 
                    ''
                }
            </div>
            
            <div class="ai-card-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>
    `;
}

/**
 * Create compact card (for multi-result searches)
 */
function createCompactCard(result) {
    const conn = result.connection;
    const angle = result.angle || result.why || '';
    
    return `
        <div class="ai-card ai-card-compact" onclick="openProfile('${conn.id}')">
            <div class="compact-content">
                <div class="compact-header">
                    <div class="compact-name">${escapeHtml(conn.name || 'Unknown')}</div>
                    ${conn.relationship !== 'Professional' ? 
                        `<span class="relationship-badge-sm">${escapeHtml(conn.relationship)}</span>` : 
                        ''
                    }
                </div>
                
                <div class="compact-role">
                    ${escapeHtml(conn.title || 'No title')}
                    ${conn.company ? ` at ${escapeHtml(conn.company)}` : ''}
                </div>
                
                ${angle ? `<div class="compact-angle">→ ${escapeHtml(angle)}</div>` : ''}
            </div>
            
            <div class="compact-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
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
 * Remove typing indicator
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
        <div class="error-container">
            <div class="error-icon">⚠️</div>
            <div class="error-content">
                <strong class="error-title">Error</strong>
                <span class="error-message">${escapeHtml(message)}</span>
            </div>
        </div>
    `;
    chat.appendChild(errorMsg);
    chat.scrollTop = chat.scrollHeight;
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Enhanced card animations
 */
function initEnhancedCardAnimations() {
    // Observe AI cards being added to DOM
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.classList && node.classList.contains('ai-msg')) {
                    // Animate cards with stagger
                    const cards = node.querySelectorAll('.ai-card');
                    cards.forEach((card, index) => {
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(10px)';
                        setTimeout(() => {
                            card.style.transition = 'all 0.3s ease';
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, index * 100);
                    });
                }
            });
        });
    });
    
    const chat = document.getElementById('ai-chat');
    if (chat) {
        observer.observe(chat, { childList: true });
    }
}

// ─── SEARCH BAR ───────────────────────────────────────────────────
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

// ─── ANIMATIONS ───────────────────────────────────────────────────
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);

/**
 * Create ultra-compact detailed card (for single profile lookups)
 * Height: ~50px | Shows name, role, relationship badge
 * Click to expand for full details
 */
function createDetailedCard(result) {
    const conn = result.connection;
    const angle = result.angle || result.why || '';
    const traits = conn.unique_traits || [];
    const cardId = `card-${conn.id}`;
    
    return `
        <div class="ai-card ai-card-detailed" id="${cardId}" onclick="toggleCardExpand('${cardId}', event)">
            <div class="ai-card-header">
                <div class="ai-card-name">${escapeHtml(conn.name || 'Unknown')}</div>
                ${conn.relationship !== 'Professional' ? 
                    `<span class="relationship-badge">${escapeHtml(conn.relationship)}</span>` : 
                    ''
                }
            </div>
            
            <div class="ai-card-role">
                ${escapeHtml(conn.title || 'No title')}${conn.company ? ` at ${escapeHtml(conn.company)}` : ''}
            </div>
            
            <div class="ai-card-footer">
                <span class="footer-item">${conn.last_contact || 'Unknown'}</span>
                ${conn.industry && conn.industry !== 'N/A' ? 
                    `<span class="footer-divider">•</span>
                     <span class="footer-item">${escapeHtml(conn.industry)}</span>` : 
                    ''
                }
            </div>
            
            ${angle ? `
                <div class="ai-card-angle">
                    <strong>Why matched:</strong> ${escapeHtml(angle)}
                </div>
            ` : ''}
            
            ${traits.length > 0 ? `
                <div class="ai-card-traits">
                    <div class="traits-label">What makes them special:</div>
                    ${traits.slice(0, 3).map(trait => 
                        `<div class="trait-item">• ${escapeHtml(trait)}</div>`
                    ).join('')}
                </div>
            ` : ''}
            
            <div class="ai-card-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>
    `;
}

/**
 * Create ultra-compact card (for multi-result searches)
 * Height: ~38px | Single line | Name + role only
 */
function createCompactCard(result) {
    const conn = result.connection;
    const angle = result.angle || result.why || '';
    const cardId = `card-${conn.id}`;
    
    return `
        <div class="ai-card ai-card-compact" id="${cardId}" onclick="openProfile('${conn.id}')">
            <div class="compact-content">
                <div class="compact-header">
                    <div class="compact-name">${escapeHtml(conn.name || 'Unknown')}</div>
                    ${conn.relationship !== 'Professional' ? 
                        `<span class="relationship-badge-sm">${escapeHtml(conn.relationship)}</span>` : 
                        ''
                    }
                </div>
                <div class="compact-role">
                    ${escapeHtml(conn.title || 'No title')}${conn.company ? ` · ${escapeHtml(conn.company)}` : ''}
                </div>
            </div>
            
            <div class="compact-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>
    `;
}

/**
 * OPTIONAL: Create ultra-minimal card (even smaller!)
 * Height: ~32px | Bare minimum info
 */
function createMinimalCard(result) {
    const conn = result.connection;
    
    return `
        <div class="ai-card ai-card-minimal" onclick="openProfile('${conn.id}')">
            <span class="minimal-name">${escapeHtml(conn.name || 'Unknown')}</span>
            <span class="minimal-meta">${escapeHtml(conn.title || 'No title')}</span>
            <div class="minimal-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>
    `;
}

/**
 * Toggle card expansion (for detailed cards only)
 * Shows/hides the angle and traits sections
 */
function toggleCardExpand(cardId, event) {
    // Don't expand if clicking to open profile
    const card = document.getElementById(cardId);
    if (!card) return;
    
    // Check if clicking on card itself (not arrow)
    const clickedArrow = event.target.closest('.ai-card-arrow');
    if (clickedArrow) {
        // Arrow click = open profile
        const connId = cardId.replace('card-', '');
        openProfile(connId);
        return;
    }
    
    // Card click = toggle expand
    event.stopPropagation();
    
    // Close all other expanded cards
    document.querySelectorAll('.ai-card-detailed.expanded').forEach(c => {
        if (c.id !== cardId) {
            c.classList.remove('expanded');
        }
    });
    
    // Toggle this card
    card.classList.toggle('expanded');
}

/**
 * Smart AI Response Display with ultra-compact cards
 */
function displaySmartAIResponse(data, originalQuery) {
    const chat = document.getElementById('ai-chat');
    if (!chat) return;
    
    const content = data.content || {};
    const intent = data.intent || 'general_search';
    const results = data.results || [];
    
    // Determine how many cards to show
    let cardCount = 0;
    let showFullCards = false;
    
    if (intent === 'profile_lookup' && results.length === 1) {
        cardCount = 1;
        showFullCards = true;
    } else if (intent === 'network_analysis') {
        cardCount = 0;
    } else if (results.length > 0) {
        cardCount = Math.min(3, results.length);
        showFullCards = false;
    }
    
    // Build message
    let message = `<div class="ai-response">`;
    
    // Title
    if (content.title) {
        message += `<div class="ai-response-title">${escapeHtml(content.title)}</div>`;
    }
    
    // Summary
    if (content.summary && content.summary !== content.title) {
        message += `<div class="ai-response-summary">${escapeHtml(content.summary)}</div>`;
    }
    
    // Main body
    if (content.body) {
        const formattedBody = formatMessageBody(content.body);
        message += `<div class="ai-response-body">${formattedBody}</div>`;
    }
    
    // Context badges
    if (content.context && content.context.length > 0) {
        message += `<div class="ai-context">`;
        content.context.forEach(ctx => {
            message += `<span class="context-badge">${escapeHtml(ctx)}</span>`;
        });
        message += `</div>`;
    }
    
    // Next steps
    if (content.next_steps && content.next_steps.length > 0) {
        message += `<div class="ai-next-steps">`;
        message += `<div class="next-steps-label">💡 Suggested actions:</div>`;
        content.next_steps.forEach(step => {
            message += `<div class="next-step-item">• ${escapeHtml(step)}</div>`;
        });
        message += `</div>`;
    }
    
    // Ultra-compact cards
    if (cardCount > 0) {
        message += `<div class="ai-results">`;
        
        for (let i = 0; i < cardCount; i++) {
            const result = results[i];
            if (showFullCards) {
                message += createDetailedCard(result);
            } else {
                message += createCompactCard(result);
            }
        }
        
        message += `</div>`;
        
        // "See more" hint
        if (results.length > cardCount) {
            
        }
    }
    
    // Metadata
    if (data.meta) {
        const count = data.meta.count || 0;
        const time = data.meta.time || 0;
        message += `
            <div class="ai-metadata">
                ${count} result${count !== 1 ? 's' : ''} • ${time}s
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
 * Format message body with markdown-like syntax
 */
function formatMessageBody(text) {
    return escapeHtml(text)
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}