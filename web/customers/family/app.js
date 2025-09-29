// AI-SERVIS Family Protection Landing Page JavaScript
// Safety-focused interactions with family connection features

document.addEventListener('DOMContentLoaded', function() {
    initializeFamilyPage();
});

function initializeFamilyPage() {
    setupLanguageSwitcher();
    setupNavigation();
    setupScrollAnimations();
    setupMobileMenu();
    setupFamilyInteractions();
    setupSafetyMonitoring();
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

// Family-specific Interactions
function setupFamilyInteractions() {
    // Family member interactions
    const familyMembers = document.querySelectorAll('.family-member');
    familyMembers.forEach(member => {
        member.addEventListener('click', function() {
            showMemberStatus(this);
        });

        member.addEventListener('mouseenter', function() {
            highlightFamilyConnection(this);
        });

        member.addEventListener('mouseleave', function() {
            resetFamilyConnection();
        });
    });

    // Safety zone interactions
    const safetyZones = document.querySelectorAll('.safety-zone');
    safetyZones.forEach(zone => {
        zone.addEventListener('click', function() {
            toggleSafetyAlert(this);
        });
    });

    // Caregiver network interactions
    const caregiverDots = document.querySelectorAll('.caregiver-dot');
    caregiverDots.forEach(dot => {
        dot.addEventListener('click', function() {
            showCaregiverInfo(this);
        });
    });

    // Connection line heartbeat effect
    const connectionLine = document.querySelector('.connection-line');
    if (connectionLine) {
        setInterval(() => {
            connectionLine.style.animation = 'none';
            setTimeout(() => {
                connectionLine.style.animation = 'heartbeat 1.5s ease-in-out';
            }, 10);
        }, 5000);
    }
}

// Safety Monitoring Features
function setupSafetyMonitoring() {
    // Simulate real-time safety monitoring
    setInterval(updateSafetyStatus, 3000);

    // Emergency button interactions
    const emergencyButtons = document.querySelectorAll('button[data-en*="Emergency"], button[data-cs*="Nouzov"]');
    emergencyButtons.forEach(button => {
        button.addEventListener('click', function() {
            triggerEmergencyAlert();
        });
    });

    // Location sharing simulation
    setupLocationSharing();
}

function updateSafetyStatus() {
    // Simulate updating family member statuses
    const familyMembers = document.querySelectorAll('.family-member');

    familyMembers.forEach((member, index) => {
        const statusIndicator = member.querySelector('.status-indicator') || createStatusIndicator(member);
        const statuses = ['safe', 'moving', 'arrived'];
        const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];

        statusIndicator.className = `status-indicator status-${randomStatus}`;

        // Update connection line based on status
        if (randomStatus === 'moving') {
            member.style.animation = 'gentlePulse 2s ease-in-out infinite';
        } else {
            member.style.animation = 'none';
        }
    });
}

function createStatusIndicator(member) {
    const indicator = document.createElement('div');
    indicator.className = 'status-indicator';
    indicator.style.cssText = `
        position: absolute;
        top: -5px;
        right: -5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
    `;
    member.style.position = 'relative';
    member.appendChild(indicator);
    return indicator;
}

function showMemberStatus(member) {
    const memberType = member.getAttribute('data-member');
    const memberName = member.querySelector('span').textContent;

    showNotification(`👨‍👩‍👧‍👦 ${memberName} is safe and connected`, 'success');

    // Create ripple effect
    createRippleEffect(member);
}

function highlightFamilyConnection(member) {
    const connectionLine = document.querySelector('.connection-line');
    if (connectionLine) {
        connectionLine.style.background = 'rgba(255, 255, 255, 0.8)';
        connectionLine.style.boxShadow = '0 0 10px rgba(45, 95, 111, 0.5)';
    }
}

function resetFamilyConnection() {
    const connectionLine = document.querySelector('.connection-line');
    if (connectionLine) {
        connectionLine.style.background = 'rgba(255, 255, 255, 0.5)';
        connectionLine.style.boxShadow = 'none';
    }
}

function toggleSafetyAlert(zone) {
    const isActive = zone.classList.contains('alert-active');

    if (isActive) {
        zone.classList.remove('alert-active');
        zone.style.borderColor = '#E8A87C';
        zone.style.animation = 'safetyZonePulse 3s ease-in-out infinite';
        showNotification('🛡️ Safety zone deactivated', 'info');
    } else {
        zone.classList.add('alert-active');
        zone.style.borderColor = '#E76F51';
        zone.style.animation = 'alertPulse 0.5s ease-in-out infinite';
        showNotification('🚨 Safety zone activated - monitoring for threats', 'warning');
    }
}

function showCaregiverInfo(dot) {
    const caregivers = ['Emergency Contact', 'Family Doctor', 'Local Police'];
    const randomCaregiver = caregivers[Math.floor(Math.random() * caregivers.length)];

    showNotification(`👥 ${randomCaregiver} notified and standing by`, 'info');

    // Highlight the dot temporarily
    dot.style.transform = 'scale(1.5)';
    dot.style.boxShadow = '0 0 15px rgba(104, 184, 148, 0.8)';

    setTimeout(() => {
        dot.style.transform = 'scale(1)';
        dot.style.boxShadow = 'none';
    }, 1000);
}

function triggerEmergencyAlert() {
    // Simulate emergency alert system
    showNotification('🚨 EMERGENCY ALERT SENT! All family members and emergency contacts notified.', 'error');

    // Flash effect on screen
    document.body.style.animation = 'emergencyFlash 0.3s ease-in-out 3';

    setTimeout(() => {
        document.body.style.animation = 'none';
    }, 1000);

    // In a real implementation, this would:
    // - Send notifications to all family members
    // - Contact emergency services
    // - Share location data
    // - Activate emergency protocols
}

function setupLocationSharing() {
    // Simulate location sharing updates
    setInterval(() => {
        const locationIndicator = document.querySelector('.location-sharing-status') || createLocationIndicator();

        if (Math.random() > 0.8) { // 20% chance of location update
            locationIndicator.style.opacity = '1';
            locationIndicator.textContent = '📍 Location updated';

            setTimeout(() => {
                locationIndicator.style.opacity = '0';
            }, 2000);
        }
    }, 10000);
}

function createLocationIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'location-sharing-status';
    indicator.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: rgba(45, 95, 111, 0.9);
        color: white;
        padding: 10px 15px;
        border-radius: 20px;
        font-size: 0.875rem;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 1000;
    `;
    document.body.appendChild(indicator);
    return indicator;
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

                // Trigger family-specific animations
                if (entry.target.classList.contains('scenario-card')) {
                    animateFamilyScenario(entry.target);
                }

                if (entry.target.classList.contains('connect-card')) {
                    animateConnectionCard(entry.target);
                }
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll('.feature-card, .scenario-card, .connect-card, .pricing-card');
    animateElements.forEach(element => {
        observer.observe(element);
    });
}

function animateFamilyScenario(card) {
    // Animate family map elements
    const familyMembers = card.querySelectorAll('.family-member');
    familyMembers.forEach((member, index) => {
        member.style.animation = `slideInFromBottom 0.6s ease-out ${index * 0.2}s both`;
    });
}

function animateConnectionCard(card) {
    // Animate connection icon
    const icon = card.querySelector('.connect-icon');
    if (icon) {
        icon.style.animation = 'bounceIn 0.8s ease-out';
    }
}

// Form Validation and Interactions
function setupFormValidation() {
    // Protection setup buttons
    const protectionButtons = document.querySelectorAll('button[data-en*="Protected"], button[data-cs*="ochranu"], button[data-en*="Protection"], button[data-cs*="ochrana"]');
    protectionButtons.forEach(button => {
        button.addEventListener('click', function() {
            showFamilyProtectionModal();
        });
    });

    // CTA buttons
    const ctaButtons = document.querySelectorAll('.cta-btn');
    ctaButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.textContent.includes('Protect') || this.textContent.includes('Family') ||
                this.textContent.includes('ochran') || this.textContent.includes('rodin')) {
                showFamilyProtectionModal();
            }
        });
    });
}

function showFamilyProtectionModal() {
    // Create family protection setup modal
    const modal = document.createElement('div');
    modal.className = 'family-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3 data-en="Setup Family Protection" data-cs="Nastavit ochranu rodiny">Nastavit ochranu rodiny</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="family-setup-visual">
                    <div class="family-circle">
                        <div class="family-member-setup" data-role="parent">
                            <i class="fas fa-user"></i>
                            <span data-en="Parent" data-cs="Rodič">Rodič</span>
                        </div>
                        <div class="family-member-setup" data-role="teen">
                            <i class="fas fa-user-graduate"></i>
                            <span data-en="Teen" data-cs="Teenager">Teenager</span>
                        </div>
                        <div class="family-member-setup" data-role="child">
                            <i class="fas fa-child"></i>
                            <span data-en="Child" data-cs="Dítě">Dítě</span>
                        </div>
                    </div>
                    <div class="protection-shield">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                </div>
                <form class="family-form">
                    <div class="form-section">
                        <h4 data-en="Family Members" data-cs="Členové rodiny">Členové rodiny</h4>
                        <div class="member-inputs">
                            <div class="member-input">
                                <label data-en="Adults" data-cs="Dospělí">Dospělí</label>
                                <input type="number" name="adults" value="2" min="1" max="10">
                            </div>
                            <div class="member-input">
                                <label data-en="Teens" data-cs="Teenageři">Teenageři</label>
                                <input type="number" name="teens" value="1" min="0" max="10">
                            </div>
                            <div class="member-input">
                                <label data-en="Children" data-cs="Děti">Děti</label>
                                <input type="number" name="children" value="0" min="0" max="10">
                            </div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h4 data-en="Safety Preferences" data-cs="Bezpečnostní preference">Bezpečnostní preference</h4>
                        <div class="safety-options">
                            <label class="option-checkbox">
                                <input type="checkbox" name="stalker_detection" checked>
                                <span data-en="Stalker Detection" data-cs="Detekce stalkera">Detekce stalkera</span>
                            </label>
                            <label class="option-checkbox">
                                <input type="checkbox" name="location_sharing" checked>
                                <span data-en="Location Sharing" data-cs="Sdílení polohy">Sdílení polohy</span>
                            </label>
                            <label class="option-checkbox">
                                <input type="checkbox" name="emergency_alerts" checked>
                                <span data-en="Emergency Alerts" data-cs="Nouzová upozornění">Nouzová upozornění</span>
                            </label>
                            <label class="option-checkbox">
                                <input type="checkbox" name="driving_monitoring">
                                <span data-en="Teen Driving Monitoring" data-cs="Sledování mladých řidičů">Sledování mladých řidičů</span>
                            </label>
                        </div>
                    </div>

                    <div class="form-section">
                        <h4 data-en="Emergency Contacts" data-cs="Nouzové kontakty">Nouzové kontakty</h4>
                        <input type="tel" name="emergency_contact" placeholder="Emergency contact phone" required>
                    </div>

                    <button type="submit" class="btn btn-primary" data-en="Activate Protection" data-cs="Aktivovat ochranu">Aktivovat ochranu</button>
                </form>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Setup modal interactions
    const closeBtn = modal.querySelector('.modal-close');
    const form = modal.querySelector('.family-form');

    closeBtn.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleFamilyProtectionSetup(new FormData(this));
        modal.remove();
    });

    // Update form labels based on current language
    updateFamilyModalLanguage(modal);

    // Setup family member interactions
    setupFamilyMemberSetup(modal);
}

function updateFamilyModalLanguage(modal) {
    const currentLang = document.querySelector('.lang-btn.active').getAttribute('data-lang');
    const elements = modal.querySelectorAll('[data-en][data-cs]');

    elements.forEach(element => {
        const text = element.getAttribute(`data-${currentLang}`);
        if (text) {
            if (element.tagName === 'INPUT') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        }
    });
}

function setupFamilyMemberSetup(modal) {
    const familyMembers = modal.querySelectorAll('.family-member-setup');

    familyMembers.forEach(member => {
        member.addEventListener('click', function() {
            // Toggle selection
            this.classList.toggle('selected');

            // Update visual feedback
            const icon = this.querySelector('i');
            if (this.classList.contains('selected')) {
                icon.style.color = '#68B984';
                this.style.boxShadow = '0 0 15px rgba(104, 184, 148, 0.5)';
            } else {
                icon.style.color = '#5D6D7E';
                this.style.boxShadow = 'none';
            }
        });
    });
}

function handleFamilyProtectionSetup(formData) {
    // Simulate family protection setup
    const familyData = Object.fromEntries(formData);
    console.log('👨‍👩‍👧‍👦 Family protection setup:', familyData);

    // Show success message
    showNotification('🛡️ Family protection activated! All members are now connected and safe.', 'success');

    // Update UI to show protection is active
    updateProtectionStatus();
}

function updateProtectionStatus() {
    // Simulate updating the protection status
    const statusIndicators = document.querySelectorAll('.status-indicator');
    statusIndicators.forEach(indicator => {
        indicator.className = 'status-indicator status-protected';
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<span class="notification-icon">${getNotificationIcon(type)}</span>${message}`;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: '🛡️',
        error: '🚨',
        warning: '⚠️',
        info: 'ℹ️'
    };
    return icons[type] || '📢';
}

// Analytics and Tracking
function setupAnalytics() {
    // Track family safety interactions
    const trackableElements = document.querySelectorAll('.family-member, .safety-zone, .caregiver-dot, .btn');
    trackableElements.forEach(element => {
        element.addEventListener('click', function() {
            const elementType = this.className.split(' ').find(cls =>
                ['family-member', 'safety-zone', 'caregiver-dot', 'btn'].includes(cls)
            );
            trackEvent('family_safety_interaction', {
                element_type: elementType,
                page_location: window.location.pathname
            });
        });
    });

    // Track form submissions
    document.addEventListener('submit', function(e) {
        trackEvent('family_form_submit', {
            form_type: e.target.className,
            page_location: window.location.pathname
        });
    });

    // Track scroll depth with family context
    let maxScroll = 0;
    window.addEventListener('scroll', function() {
        const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
        if (scrollPercent > maxScroll && scrollPercent % 25 === 0) {
            maxScroll = scrollPercent;
            trackEvent('family_scroll_depth', { percent: scrollPercent });
        }
    });
}

function trackEvent(eventName, properties = {}) {
    // In a real implementation, you would send this to your analytics service
    console.log('👨‍👩‍👧‍👦 Family event:', eventName, properties);

    // Example: Google Analytics, Mixpanel, etc.
    // gtag('event', eventName, properties);
    // mixpanel.track(eventName, properties);
}

// Family Modal Styles
const familyModalStyles = `
    .family-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(45, 95, 111, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        backdrop-filter: blur(10px);
        animation: modalFadeIn 0.3s ease-out;
    }

    .family-modal .modal-content {
        background: linear-gradient(135deg, #FEFEFE, #F0F4F8);
        border-radius: 20px;
        max-width: 600px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 40px rgba(45, 95, 111, 0.3);
        border: 2px solid rgba(45, 95, 111, 0.2);
    }

    .family-modal .modal-header {
        padding: 2rem;
        border-bottom: 1px solid #D5DBDB;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .family-modal .modal-header h3 {
        margin: 0;
        color: #2D5F6F;
        font-size: 1.5rem;
        font-weight: 700;
    }

    .family-modal .modal-close {
        background: none;
        border: none;
        font-size: 2rem;
        cursor: pointer;
        color: #5D6D7E;
        padding: 0;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s;
    }

    .family-modal .modal-close:hover {
        background: rgba(45, 95, 111, 0.1);
        color: #2D5F6F;
    }

    .family-modal .modal-body {
        padding: 2rem;
    }

    .family-setup-visual {
        text-align: center;
        margin-bottom: 2rem;
    }

    .family-circle {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .family-member-setup {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem;
        border-radius: 12px;
        background: white;
        box-shadow: 0 4px 6px rgba(45, 95, 111, 0.1);
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }

    .family-member-setup:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(45, 95, 111, 0.2);
    }

    .family-member-setup.selected {
        border-color: #68B984;
        background: rgba(104, 184, 148, 0.05);
    }

    .family-member-setup i {
        font-size: 2rem;
        color: #5D6D7E;
        transition: color 0.3s ease;
    }

    .family-member-setup.selected i {
        color: #68B984;
    }

    .family-member-setup span {
        font-size: 0.875rem;
        font-weight: 500;
        color: #2C3E50;
    }

    .protection-shield {
        font-size: 3rem;
        color: #2D5F6F;
        animation: shieldGlow 2s ease-in-out infinite alternate;
    }

    @keyframes shieldGlow {
        from { filter: drop-shadow(0 0 5px rgba(45, 95, 111, 0.3)); }
        to { filter: drop-shadow(0 0 15px rgba(45, 95, 111, 0.6)); }
    }

    .family-form {
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    .form-section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(45, 95, 111, 0.1);
    }

    .form-section h4 {
        margin: 0 0 1rem 0;
        color: #2D5F6F;
        font-size: 1.125rem;
        font-weight: 600;
    }

    .member-inputs {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
    }

    .member-input {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .member-input label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #5D6D7E;
    }

    .member-input input {
        padding: 0.5rem;
        border: 2px solid #D5DBDB;
        border-radius: 6px;
        font-size: 1rem;
        text-align: center;
        transition: border-color 0.2s;
    }

    .member-input input:focus {
        outline: none;
        border-color: #2D5F6F;
    }

    .safety-options {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .option-checkbox {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        cursor: pointer;
    }

    .option-checkbox input[type="checkbox"] {
        width: 18px;
        height: 18px;
        accent-color: #2D5F6F;
    }

    .option-checkbox span {
        font-size: 0.875rem;
        color: #2C3E50;
    }

    .family-form input[type="tel"] {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #D5DBDB;
        border-radius: 6px;
        font-size: 1rem;
        transition: border-color 0.2s;
    }

    .family-form input[type="tel"]:focus {
        outline: none;
        border-color: #2D5F6F;
    }

    .notification {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: linear-gradient(135deg, #68B984, #4A90A4);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(104, 184, 148, 0.3);
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

    .notification-error {
        background: linear-gradient(135deg, #E76F51, #E8A87C);
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

    .status-indicator {
        position: absolute;
        top: -5px;
        right: -5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
    }

    .status-safe { background: #68B984; }
    .status-moving { background: #E8A87C; animation: gentlePulse 2s ease-in-out infinite; }
    .status-arrived { background: #4A90A4; }
    .status-protected { background: #2D5F6F; box-shadow: 0 0 10px rgba(45, 95, 111, 0.8); }

    @keyframes gentlePulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    @keyframes alertPulse {
        0%, 100% { border-color: #E76F51; }
        50% { border-color: #EF4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.8); }
    }

    @keyframes emergencyFlash {
        0%, 100% { background: rgba(239, 68, 68, 0.1); }
        50% { background: rgba(239, 68, 68, 0.3); }
    }

    @keyframes slideInFromBottom {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes bounceIn {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { transform: scale(1); opacity: 1; }
    }

    @keyframes modalFadeIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }

    @media (max-width: 768px) {
        .family-modal .modal-content {
            margin: 1rem;
            width: calc(100% - 2rem);
        }

        .family-circle {
            flex-direction: column;
            gap: 1rem;
        }

        .member-inputs {
            grid-template-columns: 1fr;
        }
    }
`;

// Add family modal styles to page
const familyStyleSheet = document.createElement('style');
familyStyleSheet.textContent = familyModalStyles;
document.head.appendChild(familyStyleSheet);

// Mobile navigation styles
const familyMobileStyles = `
    .nav-menu.mobile-open {
        display: flex;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: rgba(254, 254, 254, 0.95);
        backdrop-filter: blur(10px);
        flex-direction: column;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(45, 95, 111, 0.3);
        border-top: 1px solid #D5DBDB;
        border-radius: 0 0 12px 12px;
    }

    .nav-menu.mobile-open a {
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.5);
        color: #2C3E50;
    }

    .nav-menu.mobile-open a:hover {
        color: #2D5F6F;
        border-bottom-color: rgba(45, 95, 111, 0.3);
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

const familyMobileStyleSheet = document.createElement('style');
familyMobileStyleSheet.textContent = familyMobileStyles;
document.head.appendChild(familyMobileStyleSheet);

// Error handling
window.addEventListener('error', function(e) {
    console.error('👨‍👩‍👧‍👦 Family page error:', e.error);
    trackEvent('family_error', {
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