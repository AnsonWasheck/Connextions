// Profile Dashboard JavaScript
// ────────────────────────────────────────────────────────────────

lucide.createIcons();

// Store original values for cancel functionality
let originalValues = {};
let isEditMode = false;

// ── Theme handling (shared with main app) ────────────────────────
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

// ── Edit Mode Management ──────────────────────────────────────────
function toggleEditMode() {
    isEditMode = !isEditMode;
    const banner = document.getElementById('editBanner');
    const container = document.querySelector('.profile-content');

    if (isEditMode) {
        // Enter edit mode
        banner.style.display = 'flex';
        container.classList.add('edit-mode');
        storeOriginalValues();
        enableInlineEditing();
    } else {
        // Exit edit mode
        banner.style.display = 'none';
        container.classList.remove('edit-mode');
        disableInlineEditing();
    }
}

function storeOriginalValues() {
    originalValues = {};
    const editables = document.querySelectorAll('[data-field]');
    
    editables.forEach(element => {
        const field = element.dataset.field;
        originalValues[field] = element.textContent.trim();
    });
}

function enableInlineEditing() {
    // Make text fields editable
    const textEditables = document.querySelectorAll('.editable, .editable-textarea');
    textEditables.forEach(element => {
        element.contentEditable = true;
        element.style.cursor = 'text';
        
        element.addEventListener('focus', handleEditableFocus);
        element.addEventListener('blur', handleEditableBlur);
    });

    // Make number fields editable
    const numberEditables = document.querySelectorAll('.editable-number');
    numberEditables.forEach(element => {
        element.addEventListener('click', convertToNumberInput);
    });

    // Make select fields editable
    const selectEditables = document.querySelectorAll('.editable-select');
    selectEditables.forEach(element => {
        element.addEventListener('click', convertToSelect);
    });
}

function disableInlineEditing() {
    const editables = document.querySelectorAll('[data-field]');
    editables.forEach(element => {
        element.contentEditable = false;
        element.classList.remove('editing');
        element.removeEventListener('focus', handleEditableFocus);
        element.removeEventListener('blur', handleEditableBlur);
    });
}

function handleEditableFocus(e) {
    e.target.classList.add('editing');
}

function handleEditableBlur(e) {
    e.target.classList.remove('editing');
}

// ── Convert fields to inputs ──────────────────────────────────────
function convertToNumberInput(e) {
    const element = e.currentTarget;
    const field = element.dataset.field;
    const currentValue = element.textContent.trim().replace(/[^0-9]/g, '');
    
    const input = document.createElement('input');
    input.type = 'number';
    input.value = currentValue;
    input.className = 'info-value editing';
    input.style.width = '100%';
    input.min = field === 'ai_rating' ? '1' : '0';
    input.max = field === 'ai_rating' ? '10' : '';
    
    input.addEventListener('blur', function() {
        const newValue = this.value;
        element.textContent = field === 'ai_rating' ? `${newValue}/10` : newValue;
        element.style.display = 'block';
        this.remove();
    });
    
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            this.blur();
        }
    });
    
    element.style.display = 'none';
    element.parentNode.appendChild(input);
    input.focus();
}

function convertToSelect(e) {
    const element = e.currentTarget;
    const field = element.dataset.field;
    
    if (field !== 'relationship_status') return;
    
    const currentValue = element.querySelector('.relationship-badge').textContent.trim();
    
    const select = document.createElement('select');
    select.className = 'info-value editing';
    select.style.width = '100%';
    
    const options = ['Inner Circle', 'Professional', 'Lead'];
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option;
        opt.selected = option === currentValue;
        select.appendChild(opt);
    });
    
    select.addEventListener('change', function() {
        const newValue = this.value;
        const badge = element.querySelector('.relationship-badge');
        badge.textContent = newValue;
        badge.className = `relationship-badge relationship-${newValue.replace(' ', '-')}`;
        element.style.display = 'flex';
        this.remove();
    });
    
    select.addEventListener('blur', function() {
        element.style.display = 'flex';
        this.remove();
    });
    
    element.style.display = 'none';
    element.parentNode.appendChild(select);
    select.focus();
}

// ── Save & Cancel ─────────────────────────────────────────────────
async function saveChanges() {
    const updatedData = {};
    const editables = document.querySelectorAll('[data-field]');
    
    editables.forEach(element => {
        const field = element.dataset.field;
        let value = element.textContent.trim();
        
        // Clean up special formatting
        if (field === 'ai_rating') {
            value = value.replace('/10', '');
        }
        
        if (element.classList.contains('editable-select')) {
            value = element.querySelector('.relationship-badge')?.textContent.trim() || value;
        }
        
        updatedData[field] = value;
    });

    // Get person ID from URL or page context
    const personId = getPersonIdFromPage();
    
    try {
        const response = await fetch(`/update/${personId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedData)
        });

        if (!response.ok) {
            throw new Error('Failed to save changes');
        }

        // Show success message
        showNotification('Changes saved successfully!', 'success');
        
        // Exit edit mode
        toggleEditMode();
        
        // Optionally reload to refresh all data
        setTimeout(() => {
            location.reload();
        }, 1500);

    } catch (error) {
        console.error('Error saving changes:', error);
        showNotification('Failed to save changes. Please try again.', 'error');
    }
}

function cancelEdit() {
    // Restore original values
    const editables = document.querySelectorAll('[data-field]');
    
    editables.forEach(element => {
        const field = element.dataset.field;
        if (originalValues[field]) {
            if (element.classList.contains('editable-select')) {
                const badge = element.querySelector('.relationship-badge');
                if (badge) {
                    badge.textContent = originalValues[field];
                    badge.className = `relationship-badge relationship-${originalValues[field].replace(' ', '-')}`;
                }
            } else {
                element.textContent = originalValues[field];
            }
        }
    });
    
    // Exit edit mode
    toggleEditMode();
}

// ── Quick Section Editing ─────────────────────────────────────────
function toggleEditSection(sectionName) {
    if (!isEditMode) {
        toggleEditMode();
    }
    
    // Optionally highlight the section
    const section = event.currentTarget.closest('.dashboard-card');
    section.style.boxShadow = '0 0 0 3px var(--accent-primary)';
    
    setTimeout(() => {
        section.style.boxShadow = '';
    }, 2000);
}

// ── AI Summary Regeneration ───────────────────────────────────────
async function regenerateAISummary() {
    const button = event.currentTarget;
    const icon = button.querySelector('i');
    const summaryElement = document.querySelector('[data-field="ai_summary"]');
    
    // Show loading state
    icon.style.animation = 'rotate 1s linear infinite';
    button.disabled = true;
    
    const personId = getPersonIdFromPage();
    
    try {
        const response = await fetch(`/regenerate-summary/${personId}`, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error('Failed to regenerate summary');
        }

        const data = await response.json();
        
        if (data.ai_summary) {
            summaryElement.textContent = data.ai_summary;
            showNotification('AI Summary updated!', 'success');
        }

    } catch (error) {
        console.error('Error regenerating summary:', error);
        showNotification('Failed to regenerate summary', 'error');
    } finally {
        icon.style.animation = '';
        button.disabled = false;
        lucide.createIcons();
    }
}

// ── Utility Functions ─────────────────────────────────────────────
function getPersonIdFromPage() {
    // Extract person ID from URL
    const urlParts = window.location.pathname.split('/');
    return urlParts[urlParts.length - 1];
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        padding: 16px 24px;
        background: ${type === 'success' ? 'var(--success)' : 'var(--danger)'};
        color: white;
        border-radius: 12px;
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-weight: 600;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ── Keyboard Shortcuts ────────────────────────────────────────────
document.addEventListener('keydown', function(e) {
    // Cmd/Ctrl + E to toggle edit mode
    if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        toggleEditMode();
    }
    
    // Cmd/Ctrl + S to save (when in edit mode)
    if ((e.metaKey || e.ctrlKey) && e.key === 's' && isEditMode) {
        e.preventDefault();
        saveChanges();
    }
    
    // Escape to cancel edit mode
    if (e.key === 'Escape' && isEditMode) {
        cancelEdit();
    }
});

// ── Initialize ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    lucide.createIcons();
    
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
});

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-12px);
        }
    }
`;
document.head.appendChild(style);