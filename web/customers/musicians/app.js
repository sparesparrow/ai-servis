// AI-SERVIS Musician Landing Page JavaScript
// Music-focused interactions with audio visualizations and creative elements

document.addEventListener('DOMContentLoaded', function() {
    initializeMusicPage();
});

function initializeMusicPage() {
    setupLanguageSwitcher();
    setupNavigation();
    setupScrollAnimations();
    setupMobileMenu();
    setupMusicInteractions();
    setupAudioVisualizer();
    setupFormValidation();
    setupAnalytics();
}

// Language Switching
function setupLanguageSwitcher() {
    const langButtons = document.querySelectorAll('.lang-btn');
    const elements = document.querySelectorAll('[data-en][data-cs]');

    langButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');

            // Update button states
            langButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Update content
            elements.forEach(element => {
                const text = element.getAttribute(`data-${lang}`);
                if (text) {
                    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                        element.placeholder = text;
                    } else if (element.tagName === 'IMG') {
                        element.alt = text;
                    } else {
                        element.textContent = text;
                    }
                }
            });

            // Store language preference
            localStorage.setItem('preferred-language', lang);
        });
    });

    // Load saved language preference
    const savedLang = localStorage.getItem('preferred-language') || 'cs';
    const savedButton = document.querySelector(`[data-lang="${savedLang}"]`);
    if (savedButton) {
        savedButton.click();
    }
}

// Navigation
function setupNavigation() {
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.nav-menu a');

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Smooth scrolling for anchor links
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);

            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Mobile Menu
function setupMobileMenu() {
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', function() {
            navMenu.classList.toggle('mobile-open');
            this.classList.toggle('active');

            // Animate hamburger icon
            const spans = this.querySelectorAll('span');
            if (this.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }
}

// Music-specific Interactions
function setupMusicInteractions() {
    // Play button interactions
    const playButtons = document.querySelectorAll('.play-button');
    playButtons.forEach(button => {
        button.addEventListener('click', function() {
            const icon = this.querySelector('i');
            const isPlaying = icon.classList.contains('fa-pause');

            if (isPlaying) {
                icon.classList.remove('fa-pause');
                icon.classList.add('fa-play');
                pauseAudioDemo();
            } else {
                icon.classList.remove('fa-play');
                icon.classList.add('fa-pause');
                playAudioDemo();
            }

            // Add ripple effect
            createRippleEffect(this);
        });
    });

    // Studio card hover effects
    const studioCards = document.querySelectorAll('.studio-card');
    studioCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            playHoverSound();
        });
    });

    // Feature card click effects
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('click', function() {
            createParticleEffect(this);
        });
    });
}

// Audio Visualizer
function setupAudioVisualizer() {
    // Create dynamic visualizer bars
    const visualizer = document.querySelector('.hero-visualizer');
    if (visualizer) {
        // Add more bars for better effect
        for (let i = 0; i < 10; i++) {
            const bar = document.createElement('div');
            bar.className = 'bar';
            bar.style.animationDelay = `${i * 0.1}s`;
            bar.style.height = `${Math.random() * 60 + 20}px`;
            visualizer.appendChild(bar);
        }

        // Update visualizer based on scroll
        window.addEventListener('scroll', function() {
            const scrollPercent = window.scrollY / (document.body.scrollHeight - window.innerHeight);
            const bars = document.querySelectorAll('.hero-visualizer .bar');

            bars.forEach((bar, index) => {
                const baseHeight = 20 + Math.sin(scrollPercent * Math.PI * 2 + index * 0.5) * 30;
                bar.style.height = `${Math.max(20, baseHeight)}px`;
            });
        });
    }

    // Add visualizer to other sections
    createMiniVisualizers();
}

function createMiniVisualizers() {
    const sections = document.querySelectorAll('.features, .studio, .pricing');

    sections.forEach(section => {
        const visualizer = document.createElement('div');
        visualizer.className = 'mini-visualizer';
        visualizer.innerHTML = `
            <div class="mini-bar"></div>
            <div class="mini-bar"></div>
            <div class="mini-bar"></div>
            <div class="mini-bar"></div>
            <div class="mini-bar"></div>
        `;

        section.appendChild(visualizer);

        // Animate mini visualizers
        const bars = visualizer.querySelectorAll('.mini-bar');
        bars.forEach((bar, index) => {
            bar.style.animation = `miniWave 2s ease-in-out infinite`;
            bar.style.animationDelay = `${index * 0.2}s`;
        });
    });
}

// Audio Demo Functions
function playAudioDemo() {
    // Simulate audio playback with visual feedback
    const visualizer = document.querySelector('.hero-visualizer');
    if (visualizer) {
        visualizer.classList.add('playing');
    }

    // In a real implementation, you would play actual audio
    console.log('🎵 Playing audio demo...');

    // Show notification
    showNotification('🎧 Audio demo started! Feel the beat...', 'success');
}

function pauseAudioDemo() {
    const visualizer = document.querySelector('.hero-visualizer');
    if (visualizer) {
        visualizer.classList.remove('playing');
    }

    console.log('⏸️ Audio demo paused');
}

function playHoverSound() {
    // In a real implementation, you would play a subtle sound effect
    console.log('🔊 Hover sound effect');
}

// Visual Effects
function createRippleEffect(element) {
    const ripple = document.createElement('div');
    ripple.className = 'ripple-effect';
    element.appendChild(ripple);

    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';

    setTimeout(() => ripple.remove(), 600);
}

function createParticleEffect(element) {
    for (let i = 0; i < 10; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 0.5 + 's';

        element.appendChild(particle);

        setTimeout(() => particle.remove(), 1000);
    }
}

// Scroll Animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');

                // Trigger music animations
                if (entry.target.classList.contains('feature-card')) {
                    triggerCardAnimation(entry.target);
                }
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll('.feature-card, .performance-case, .studio-card, .pricing-card');
    animateElements.forEach(element => {
        observer.observe(element);
    });
}

function triggerCardAnimation(card) {
    // Add musical animation to cards
    const icon = card.querySelector('.feature-icon, .studio-icon');
    if (icon) {
        icon.style.animation = 'none';
        setTimeout(() => {
            icon.style.animation = 'bounce 0.6s ease-in-out';
        }, 10);
    }
}

// Form Validation and Interactions
function setupFormValidation() {
    // Demo request buttons
    const demoButtons = document.querySelectorAll('button[data-en*="Setup"], button[data-cs*="studio"], button[data-en*="Start"], button[data-cs*="Začít"]');
    demoButtons.forEach(button => {
        button.addEventListener('click', function() {
            showMusicDemoModal();
        });
    });

    // CTA buttons
    const ctaButtons = document.querySelectorAll('.cta-btn');
    ctaButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.textContent.includes('Create') || this.textContent.includes('tvořit')) {
                showMusicDemoModal();
            }
        });
    });
}

function showMusicDemoModal() {
    // Create music-focused modal
    const modal = document.createElement('div');
    modal.className = 'music-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3 data-en="Start Your Music Revolution" data-cs="Začněte svou hudební revoluci">Začněte svou hudební revoluci</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="demo-visualizer">
                    <div class="demo-bar"></div>
                    <div class="demo-bar"></div>
                    <div class="demo-bar"></div>
                    <div class="demo-bar"></div>
                    <div class="demo-bar"></div>
                </div>
                <form class="music-form">
                    <div class="form-group">
                        <label data-en="Artist/Band Name" data-cs="Jméno umělce/kapely">Jméno umělce/kapely</label>
                        <input type="text" name="artist_name" required>
                    </div>
                    <div class="form-group">
                        <label data-en="Email" data-cs="E-mail">E-mail</label>
                        <input type="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label data-en="Genre" data-cs="Žánr">Žánr</label>
                        <select name="genre">
                            <option value="electronic" data-en="Electronic" data-cs="Elektronická">Elektronická</option>
                            <option value="rock" data-en="Rock" data-cs="Rock">Rock</option>
                            <option value="hip-hop" data-en="Hip-Hop" data-cs="Hip-Hop">Hip-Hop</option>
                            <option value="jazz" data-en="Jazz" data-cs="Jazz">Jazz</option>
                            <option value="classical" data-en="Classical" data-cs="Klasická">Klasická</option>
                            <option value="other" data-en="Other" data-cs="Jiný">Jiný</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label data-en="Current Setup" data-cs="Současné vybavení">Současné současné vybavení</label>
                        <textarea name="current_setup" placeholder="Tell us about your current music setup..." rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary" data-en="Start Creating Music" data-cs="Začít tvořit hudbu">Začít tvořit hudbu</button>
                </form>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Setup modal interactions
    const closeBtn = modal.querySelector('.modal-close');
    const form = modal.querySelector('.music-form');

    closeBtn.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleMusicDemoRequest(new FormData(this));
        modal.remove();
    });

    // Update form labels based on current language
    updateMusicModalLanguage(modal);

    // Start demo visualizer
    startDemoVisualizer(modal);
}

function updateMusicModalLanguage(modal) {
    const currentLang = document.querySelector('.lang-btn.active').getAttribute('data-lang');
    const elements = modal.querySelectorAll('[data-en][data-cs]');

    elements.forEach(element => {
        const text = element.getAttribute(`data-${currentLang}`);
        if (text) {
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        }
    });
}

function startDemoVisualizer(modal) {
    const bars = modal.querySelectorAll('.demo-bar');
    bars.forEach((bar, index) => {
        bar.style.animation = `demoWave 1s ease-in-out infinite`;
        bar.style.animationDelay = `${index * 0.1}s`;
    });
}

function handleMusicDemoRequest(formData) {
    // Simulate form submission
    console.log('🎵 Music demo request submitted:', Object.fromEntries(formData));

    // Show success message
    showNotification('🎸 Welcome to the music revolution! We\'ll contact you within 24 hours.', 'success');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<span class="notification-icon">${type === 'success' ? '🎵' : '⚠️'}</span>${message}`;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Analytics and Tracking
function setupAnalytics() {
    // Track music interactions
    const trackableElements = document.querySelectorAll('.play-button, .feature-card, .studio-card, .btn');
    trackableElements.forEach(element => {
        element.addEventListener('click', function() {
            const elementType = this.className.split(' ').find(cls =>
                ['play-button', 'feature-card', 'studio-card', 'btn'].includes(cls)
            );
            trackEvent('music_interaction', {
                element_type: elementType,
                page_location: window.location.pathname
            });
        });
    });

    // Track form submissions
    document.addEventListener('submit', function(e) {
        trackEvent('music_form_submit', {
            form_type: e.target.className,
            page_location: window.location.pathname
        });
    });

    // Track scroll depth with music context
    let maxScroll = 0;
    window.addEventListener('scroll', function() {
        const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
        if (scrollPercent > maxScroll && scrollPercent % 25 === 0) {
            maxScroll = scrollPercent;
            trackEvent('music_scroll_depth', { percent: scrollPercent });
        }
    });
}

function trackEvent(eventName, properties = {}) {
    // In a real implementation, you would send this to your analytics service
    console.log('🎵 Music event:', eventName, properties);

    // Example: Google Analytics, Mixpanel, etc.
    // gtag('event', eventName, properties);
    // mixpanel.track(eventName, properties);
}

// Music Modal Styles
const musicModalStyles = `
    .music-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(15, 15, 35, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        backdrop-filter: blur(10px);
        animation: modalFadeIn 0.3s ease-out;
    }

    .music-modal .modal-content {
        background: linear-gradient(135deg, #0F0F23, #1A1A2E);
        border-radius: 20px;
        max-width: 500px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.3);
        border: 1px solid rgba(139, 92, 246, 0.2);
    }

    .music-modal .modal-header {
        padding: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .music-modal .modal-header h3 {
        margin: 0;
        color: #8B5CF6;
        font-size: 1.5rem;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
    }

    .music-modal .modal-close {
        background: none;
        border: none;
        font-size: 2rem;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.6);
        padding: 0;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s;
    }

    .music-modal .modal-close:hover {
        background: rgba(139, 92, 246, 0.2);
        color: #8B5CF6;
    }

    .music-modal .modal-body {
        padding: 2rem;
    }

    .demo-visualizer {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        gap: 4px;
        height: 60px;
        margin-bottom: 2rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }

    .demo-bar {
        width: 6px;
        background: linear-gradient(180deg, #8B5CF6, #06B6D4);
        border-radius: 3px;
        animation: demoWave 1s ease-in-out infinite;
    }

    @keyframes demoWave {
        0%, 100% { height: 10px; }
        50% { height: 40px; }
    }

    .music-form {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .music-form .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .music-form .form-group label {
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.875rem;
    }

    .music-form .form-group input,
    .music-form .form-group select,
    .music-form .form-group textarea {
        padding: 0.75rem;
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        font-size: 1rem;
        background: rgba(255, 255, 255, 0.05);
        color: white;
        transition: border-color 0.2s;
    }

    .music-form .form-group input:focus,
    .music-form .form-group select:focus,
    .music-form .form-group textarea:focus {
        outline: none;
        border-color: #8B5CF6;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
    }

    .music-form .form-group textarea {
        resize: vertical;
        min-height: 80px;
    }

    .notification {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        z-index: 10001;
        transform: translateX(100%);
        transition: transform 0.3s ease-out;
        max-width: 400px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification-icon {
        font-size: 1.25rem;
    }

    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    }

    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: #8B5CF6;
        border-radius: 50%;
        animation: particleFloat 1s ease-out forwards;
        pointer-events: none;
    }

    @keyframes particleFloat {
        to {
            transform: translateY(-20px);
            opacity: 0;
        }
    }

    .mini-visualizer {
        position: absolute;
        bottom: 2rem;
        right: 2rem;
        display: flex;
        align-items: flex-end;
        gap: 2px;
        opacity: 0.3;
    }

    .mini-bar {
        width: 3px;
        height: 20px;
        background: rgba(139, 92, 246, 0.6);
        border-radius: 2px;
    }

    @keyframes miniWave {
        0%, 100% { height: 10px; }
        50% { height: 30px; }
    }

    @keyframes modalFadeIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }

    @media (max-width: 768px) {
        .music-modal .modal-content {
            margin: 1rem;
            width: calc(100% - 2rem);
        }

        .demo-visualizer {
            height: 40px;
        }
    }
`;

// Add music modal styles to page
const musicStyleSheet = document.createElement('style');
musicStyleSheet.textContent = musicModalStyles;
document.head.appendChild(musicStyleSheet);

// Mobile navigation styles
const musicMobileStyles = `
    .nav-menu.mobile-open {
        display: flex;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(10px);
        flex-direction: column;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border-top: 1px solid rgba(45, 55, 72, 0.5);
        border-radius: 0 0 12px 12px;
    }

    .nav-menu.mobile-open a {
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.8);
    }

    .nav-menu.mobile-open a:hover {
        color: #8B5CF6;
        border-bottom-color: rgba(139, 92, 246, 0.3);
    }

    .nav-menu.mobile-open a:last-child {
        border-bottom: none;
    }

    @media (max-width: 768px) {
        .container {
            padding: 0 1rem;
        }

        .mobile-menu-toggle.active span:nth-child(1) {
            transform: rotate(45deg) translate(5px, 5px);
        }

        .mobile-menu-toggle.active span:nth-child(2) {
            opacity: 0;
        }

        .mobile-menu-toggle.active span:nth-child(3) {
            transform: rotate(-45deg) translate(7px, -6px);
        }
    }
`;

const musicMobileStyleSheet = document.createElement('style');
musicMobileStyleSheet.textContent = musicMobileStyles;
document.head.appendChild(musicMobileStyleSheet);

// Error handling
window.addEventListener('error', function(e) {
    console.error('🎵 Music page error:', e.error);
    trackEvent('music_error', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno
    });
});

// Performance optimization: Lazy load images
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
setupLazyLoading();

// Service worker registration (for PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered'))
        //     .catch(error => console.log('SW registration failed'));
    });
}