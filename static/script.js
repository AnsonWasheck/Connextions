lucide.createIcons();

window.addEventListener('DOMContentLoaded', function() {
    populateFilters();
});

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
    industries.forEach(industry => {
        const option = document.createElement('option');
        option.value = industry;
        option.textContent = industry;
        industryFilter.appendChild(option);
    });
}

function toggleExpand(row) {
    const details = row.querySelector('.connection-details');
    const icon = row.querySelector('.expand-icon');
    const isExpanded = details.classList.contains('show');
    
    // Close all others first
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

function openModal() { 
    document.getElementById('add-modal').classList.add('show');
    lucide.createIcons();
}

function closeModal() { 
    document.getElementById('add-modal').classList.remove('show'); 
}

function quickQuery(query) {
    document.getElementById('ai-query').value = query;
    runAISearch();
}

async function runAISearch() {
    const input   = document.getElementById('ai-query');
    const chat    = document.getElementById('ai-chat');
    const sendBtn = document.getElementById('send-btn');
    const query   = input.value.trim();
    
    if (!query) return;

    const userMsg = document.createElement('div');
    userMsg.className = 'user-msg';
    userMsg.textContent = query;
    chat.appendChild(userMsg);
    input.value = "";

    sendBtn.disabled = true;

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

function sortConnections() {
    const sortValue = document.getElementById('sort-filter').value;
    const container = document.getElementById('connections-list');
    const rows = Array.from(container.querySelectorAll('.connection-row'));
    
    rows.sort((a, b) => {
        switch(sortValue) {
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

function filterConnections() {
    const industryValue    = document.getElementById('industry-filter').value;
    const momentumValue    = document.getElementById('momentum-filter').value;
    const relationshipValue = document.getElementById('relationship-filter').value;
    
    const rows = document.querySelectorAll('.connection-row');
    
    rows.forEach(row => {
        const industry    = row.dataset.industry;
        const momentum    = row.dataset.momentum;
        const relationship = row.dataset.relationship;
        
        const industryMatch    = industryValue === 'all' || industry === industryValue;
        const momentumMatch    = momentumValue === 'all' || momentum === momentumValue;
        const relationshipMatch = relationshipValue === 'all' || relationship === relationshipValue;
        
        if (industryMatch && momentumMatch && relationshipMatch) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
        // ── Dark-mode toggle ────────────────────────────────
        function toggleTheme() {
            const html = document.documentElement;
            const newTheme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            document.getElementById('theme-icon-light').style.display = newTheme === 'dark' ? 'none'  : 'block';
            document.getElementById('theme-icon-dark').style.display  = newTheme === 'dark' ? 'block' : 'none';
            lucide.createIcons();
        }

        document.addEventListener('DOMContentLoaded', function () {
            const saved = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', saved);
            document.getElementById('theme-icon-light').style.display = saved === 'dark' ? 'none'  : 'block';
            document.getElementById('theme-icon-dark').style.display  = saved === 'dark' ? 'block' : 'none';
            lucide.createIcons();
        });

        // ── Submit handler – fetch POST then hard reload ────
        async function submitNewConnection() {
            // Quick validation: name is required
            const nameEl = document.getElementById('f-full_name');
            if (!nameEl.value.trim()) {
                nameEl.style.borderColor = 'var(--danger)';
                nameEl.focus();
                return;
            }

            // Field-name → element-id mapping (matches what the original <form> sent)
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

            // Disable button to prevent double-submit
            const btn = document.querySelector('#add-form .add-btn');
            btn.disabled = true;
            btn.style.opacity = '0.6';

            try {
                const res = await fetch('/add', {
                    method: 'POST',
                    body:   formData
                });

                if (!res.ok) throw new Error('Server responded ' + res.status);

                // ✅ Success – hard reload so Jinja template re-renders with new row
                window.location.reload();

            } catch (err) {
                console.error('Add connection failed:', err);
                btn.disabled = false;
                btn.style.opacity = '1';
                // Show a little inline error so the user knows something went wrong
                alert('Something went wrong while saving. Check the console for details.');
            }
        }
}
