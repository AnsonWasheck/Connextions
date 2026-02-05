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
    
    // Update icon visibility
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    
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
    const darkIcon = document.getElementById('theme-icon-dark');
    
    if (savedTheme === 'dark') {
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'block';
    }
    
    lucide.createIcons();
    
    // Initialize particles
    createParticles();
    
    // Add input animations
    setupInputAnimations();
});

// ===== ANIMATED PARTICLES BACKGROUND =====
function createParticles() {
    const container = document.getElementById('particles');
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random size between 3px and 8px
        const size = Math.random() * 5 + 3;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        // Random position
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        
        // Random animation duration and delay
        const duration = Math.random() * 10 + 15;
        const delay = Math.random() * 5;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        
        container.appendChild(particle);
    }
}

// ===== TAB SWITCHING =====
function switchTab(tab) {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const indicator = document.getElementById('tab-indicator');
    
    // Get current active form for smooth transition
    const currentForm = document.querySelector('.auth-form.active');
    
    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        indicator.classList.remove('register');
        
        // Smooth fade out current form
        if (currentForm) {
            currentForm.style.opacity = '0';
            currentForm.style.transform = 'translateY(10px)';
        }
        
        setTimeout(() => {
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
            
            // Reset the form that's being hidden
            if (registerForm) {
                registerForm.style.opacity = '';
                registerForm.style.transform = '';
            }
        }, 200);
        
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        indicator.classList.add('register');
        
        // Smooth fade out current form
        if (currentForm) {
            currentForm.style.opacity = '0';
            currentForm.style.transform = 'translateY(10px)';
        }
        
        setTimeout(() => {
            registerForm.classList.add('active');
            loginForm.classList.remove('active');
            
            // Reset the form that's being hidden
            if (loginForm) {
                loginForm.style.opacity = '';
                loginForm.style.transform = '';
            }
        }, 200);
    }
    
    // Re-initialize icons after form switch
    setTimeout(() => lucide.createIcons(), 250);
}

// ===== PASSWORD VISIBILITY TOGGLE =====
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.parentElement.querySelector('.toggle-password');
    const icon = button.querySelector('svg');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.setAttribute('data-lucide', 'eye-off');
    } else {
        input.type = 'password';
        icon.setAttribute('data-lucide', 'eye');
    }
    
    lucide.createIcons();
}

// ===== PASSWORD STRENGTH CHECKER =====
function checkPasswordStrength(password) {
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');
    
    if (!strengthFill || !strengthText) return;
    
    let strength = 0;
    let text = '';
    
    if (password.length === 0) {
        strengthFill.style.width = '0%';
        strengthFill.className = 'strength-fill';
        strengthText.textContent = 'Enter a password';
        return;
    }
    
    // Check length
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Check for uppercase
    if (/[A-Z]/.test(password)) strength++;
    
    // Check for lowercase
    if (/[a-z]/.test(password)) strength++;
    
    // Check for numbers
    if (/\d/.test(password)) strength++;
    
    // Check for special characters
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // Determine strength level
    if (strength <= 2) {
        strengthFill.className = 'strength-fill weak';
        text = 'Weak password';
    } else if (strength <= 4) {
        strengthFill.className = 'strength-fill medium';
        text = 'Medium password';
    } else {
        strengthFill.className = 'strength-fill strong';
        text = 'Strong password';
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

// ===== FORM VALIDATION =====
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

// ===== LOGIN FORM HANDLER =====
function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const button = event.target.querySelector('.submit-btn');
    
    // Validation
    if (!validateEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        return false;
    }
    
    if (!validatePassword(password)) {
        showToast('Password must be at least 8 characters', 'error');
        return false;
    }
    
    // Add loading state
    button.classList.add('loading');
    
    // Simulate API call (replace with actual endpoint)
    setTimeout(() => {
        // Success - you would handle the actual response here
        showToast('Login successful! Redirecting...', 'success');
        
        // Redirect after delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);
    }, 1500);
    
    return false;
}

// ===== REGISTER FORM HANDLER =====
function handleRegister(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('first-name').value;
    const lastName = document.getElementById('last-name').value;
    const email = document.getElementById('register-email').value;
    const company = document.getElementById('company-name').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const termsAccepted = document.querySelector('input[name="terms"]').checked;
    const button = event.target.querySelector('.submit-btn');
    
    // Validation
    if (!firstName || !lastName) {
        showToast('Please enter your full name', 'error');
        return false;
    }
    
    if (!validateEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        return false;
    }
    
    if (!company) {
        showToast('Please enter your company name', 'error');
        return false;
    }
    
    if (!validatePassword(password)) {
        showToast('Password must be at least 8 characters', 'error');
        return false;
    }
    
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return false;
    }
    
    if (!termsAccepted) {
        showToast('Please accept the terms and conditions', 'error');
        return false;
    }
    
    // Add loading state
    button.classList.add('loading');
    
    // Simulate API call (replace with actual endpoint)
    setTimeout(() => {
        // Success - you would handle the actual response here
        showToast('Account created successfully! Redirecting...', 'success');
        
        // Redirect after delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);
    }, 1500);
    
    return false;
}

// ===== SOCIAL LOGIN =====
function socialLogin(provider) {
    showToast(`Connecting to ${provider}...`, 'success');
    
    // Add your social login logic here
    setTimeout(() => {
        // window.location.href = `/auth/${provider}`;
    }, 1000);
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToast = document.querySelector('.message-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `message-toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 'alert-circle';
    
    toast.innerHTML = `
        <i data-lucide="${icon}" size="20"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    lucide.createIcons();
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3300);
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
    // Alt + L for login tab
    if (e.altKey && e.key === 'l') {
        e.preventDefault();
        switchTab('login');
    }
    
    // Alt + R for register tab
    if (e.altKey && e.key === 'r') {
        e.preventDefault();
        switchTab('register');
    }
    
    // Alt + D for dark mode toggle
    if (e.altKey && e.key === 'd') {
        e.preventDefault();
        toggleTheme();
    }
});

// ===== SMOOTH SCROLL POLYFILL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===== PERFORMANCE OPTIMIZATIONS =====
// Debounce function for input events
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

// Apply debounce to password strength checker
const debouncedPasswordCheck = debounce(checkPasswordStrength, 300);
const registerPasswordInput = document.getElementById('register-password');
if (registerPasswordInput) {
    registerPasswordInput.addEventListener('input', (e) => {
        debouncedPasswordCheck(e.target.value);
    });
}

// ===== FORM FIELD AUTO-FORMAT =====
// Auto-format email to lowercase
document.querySelectorAll('input[type="email"]').forEach(input => {
    input.addEventListener('blur', function() {
        this.value = this.value.toLowerCase().trim();
    });
});

// ===== ACCESSIBILITY ENHANCEMENTS =====
// Add focus visible styles for keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-nav');
    }
});

document.addEventListener('mousedown', () => {
    document.body.classList.remove('keyboard-nav');
});

// ===== ERROR HANDLING =====
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    // You could send this to an error tracking service
});

// ===== ANALYTICS EVENTS =====
function trackEvent(eventName, eventData = {}) {
    // Add your analytics tracking here
    console.log('Event tracked:', eventName, eventData);
    
    // Example: Google Analytics
    // if (typeof gtag !== 'undefined') {
    //     gtag('event', eventName, eventData);
    // }
}

// Track tab switches
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');

if (loginTab) {
    loginTab.addEventListener('click', () => {
        trackEvent('tab_switch', { tab: 'login' });
    });
}

if (registerTab) {
    registerTab.addEventListener('click', () => {
        trackEvent('tab_switch', { tab: 'register' });
    });
}

// Track social login attempts
document.querySelectorAll('.social-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const provider = e.currentTarget.textContent.trim();
        trackEvent('social_login_attempt', { provider });
    });
});

// ===== COPY PREVENTION (OPTIONAL SECURITY) =====
// Uncomment if you want to prevent password field copying
// document.querySelectorAll('input[type="password"]').forEach(input => {
//     input.addEventListener('copy', (e) => {
//         e.preventDefault();
//         showToast('Copying passwords is not allowed', 'error');
//     });
// });

// ===== AUTOFOCUS FIRST FIELD =====
setTimeout(() => {
    const firstInput = document.querySelector('.auth-form.active input:not([type="checkbox"])');
    if (firstInput) {
        firstInput.focus();
    }
}, 500);

console.log('Vertex Auth System Initialized ✓');