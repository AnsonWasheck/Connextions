// Initialize Lucide icons
if (typeof lucide !== 'undefined') {
    lucide.createIcons();
}

// ===== THEME MANAGEMENT =====
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon   = document.getElementById('theme-icon-dark');
    
    if (newTheme === 'dark') {
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'block';
    } else {
        lightIcon.style.display = 'block';
        darkIcon.style.display = 'none';
    }
    
    lucide.createIcons();
}

// Load saved theme
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon  = document.getElementById('theme-icon-dark');
    
    if (savedTheme === 'dark') {
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'block';
    }
    
    lucide.createIcons();
    
    createParticles();
    setupInputAnimations();
    
    // Autofocus first input
    setTimeout(() => {
        const firstInput = document.querySelector('.auth-form.active input:not([type="checkbox"])');
        if (firstInput) firstInput.focus();
    }, 500);
});

// ===== ANIMATED PARTICLES BACKGROUND =====
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 5 + 3;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        
        const duration = Math.random() * 10 + 15;
        const delay = Math.random() * 5;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        
        container.appendChild(particle);
    }
}

// ===== TAB SWITCHING =====
function switchTab(tab) {
    const loginTab     = document.getElementById('login-tab');
    const registerTab  = document.getElementById('register-tab');
    const loginForm    = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const indicator    = document.getElementById('tab-indicator');
    
    const currentForm = document.querySelector('.auth-form.active');
    
    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        indicator.classList.remove('register');
        
        if (currentForm) {
            currentForm.style.opacity = '0';
            currentForm.style.transform = 'translateY(10px)';
        }
        
        setTimeout(() => {
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
            if (registerForm) {
                registerForm.style.opacity = '';
                registerForm.style.transform = '';
            }
        }, 200);
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        indicator.classList.add('register');
        
        if (currentForm) {
            currentForm.style.opacity = '0';
            currentForm.style.transform = 'translateY(10px)';
        }
        
        setTimeout(() => {
            registerForm.classList.add('active');
            loginForm.classList.remove('active');
            if (loginForm) {
                loginForm.style.opacity = '';
                loginForm.style.transform = '';
            }
        }, 200);
    }
    
    setTimeout(() => lucide.createIcons(), 250);
}

// ===== PASSWORD VISIBILITY TOGGLE =====
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const button = input.parentElement.querySelector('.toggle-password');
    const icon = button?.querySelector('svg');
    
    if (!button || !icon) return;
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.setAttribute('data-lucide', 'eye-off');
    } else {
        input.type = 'password';
        icon.setAttribute('data-lucide', 'eye');
    }
    
    lucide.createIcons();
}

// ===== PASSWORD STRENGTH VISUALIZER =====
function checkPasswordStrength(password) {
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');
    
    if (!strengthFill || !strengthText) return;
    
    if (password.length === 0) {
        strengthFill.style.width = '0%';
        strengthFill.className = 'strength-fill';
        strengthText.textContent = 'Enter a password';
        return;
    }
    
    let strength = 0;
    
    if (password.length >= 8)  strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/\d/.test(password))    strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    let text = '';
    if (strength <= 2) {
        strengthFill.className = 'strength-fill weak';
        text = 'Weak';
    } else if (strength <= 4) {
        strengthFill.className = 'strength-fill medium';
        text = 'Medium';
    } else {
        strengthFill.className = 'strength-fill strong';
        text = 'Strong';
    }
    
    strengthText.textContent = text;
}

// ===== INPUT ANIMATIONS =====
function setupInputAnimations() {
    const inputs = document.querySelectorAll('input, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'translateY(-2px)';
            this.parentElement.style.transition = 'transform 0.3s ease';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'translateY(0)';
        });
    });
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'success') {
    const existing = document.querySelector('.message-toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = `message-toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 'alert-circle';
    
    toast.innerHTML = `
        <i data-lucide="${icon}" size="20"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => toast.remove(), 3300);
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key === 'l') {
        e.preventDefault();
        switchTab('login');
    }
    if (e.altKey && e.key === 'r') {
        e.preventDefault();
        switchTab('register');
    }
    if (e.altKey && e.key === 'd') {
        e.preventDefault();
        toggleTheme();
    }
});

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ===== DEBOUNCED PASSWORD STRENGTH =====
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedCheck = debounce(checkPasswordStrength, 300);
const registerPwInput = document.getElementById('register-password');
if (registerPwInput) {
    registerPwInput.addEventListener('input', (e) => {
        debouncedCheck(e.target.value);
    });
}

// ===== ACCESSIBILITY HINT =====
document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') document.body.classList.add('keyboard-nav');
});
document.addEventListener('mousedown', () => {
    document.body.classList.remove('keyboard-nav');
});

console.log('Vertex Visual Auth UI Initialized ✓');