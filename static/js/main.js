// ============================================
// LuxeEstate - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function () {
    initializeThemeToggle();
    initializeEventListeners();
    initializeBootstrapFallbacks();
    initializeTooltips();
    initializeMagicalFloaters();
    initializeAiConcierge();
    initializeMobileOptimizations();
});

function initializeThemeToggle() {
    const toggleButton = document.getElementById('themeToggle');
    if (!toggleButton) return;

    const root = document.documentElement;
    const THEME_KEY = 'luxeTheme';
    const MAGICAL_THEME = 'magical';
    const COSMIC_THEME = 'cosmic';

    const setTheme = (themeName, persist = false) => {
        const nextTheme = themeName; // Use the themeName directly
        root.setAttribute('data-theme', nextTheme);

        if (persist) {
            try {
                localStorage.setItem(THEME_KEY, nextTheme);
            } catch (error) {
                console.warn('Could not persist theme preference:', error);
            }
        }

        const nextLabel = nextTheme === MAGICAL_THEME ? 'Magical' : 'Cosmic';
        const nextAria = nextTheme === MAGICAL_THEME
            ? 'Switch to Cosmic theme'
            : 'Switch to Magical theme';

        toggleButton.setAttribute('aria-label', nextAria);
        toggleButton.setAttribute('title', nextAria);

        const labelElement = toggleButton.querySelector('.theme-toggle-label');
        if (labelElement) {
            labelElement.textContent = nextLabel;
        }
    };

    const currentTheme = root.getAttribute('data-theme');
    setTheme(currentTheme === MAGICAL_THEME ? MAGICAL_THEME : COSMIC_THEME);

    toggleButton.addEventListener('click', () => {
        const activeTheme = root.getAttribute('data-theme') === MAGICAL_THEME ? MAGICAL_THEME : COSMIC_THEME;
        const toggledTheme = activeTheme === MAGICAL_THEME ? COSMIC_THEME : MAGICAL_THEME;
        setTheme(toggledTheme, true);
    });
}

// ============================================
// Event Listeners
// ============================================

function initializeEventListeners() {
    // Favorite button toggle
    const favoriteButtons = document.querySelectorAll('.btn-favorite, .btn-favorite-side');
    favoriteButtons.forEach(btn => {
        btn.addEventListener('click', toggleFavorite);
    });

    // Comparison button toggle
    const compareButtons = document.querySelectorAll('.btn-compare');
    compareButtons.forEach(btn => {
        btn.addEventListener('click', toggleComparison);
    });

    // Search form submission
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // Image search upload + redirect flow
    initializeImageSearch();

    // Price range slider
    const priceSliders = document.querySelectorAll('.price-range');
    priceSliders.forEach(slider => {
        slider.addEventListener('input', updatePriceDisplay);
    });
}

function initializeImageSearch() {
    const searchImageInput = document.getElementById('searchImageInput');
    const searchByImageBtn = document.getElementById('searchByImageBtn');
    const imageSearchStatus = document.getElementById('imageSearchStatus');

    if (!searchImageInput || !searchByImageBtn) return;

    const setStatus = (message, type = 'info') => {
        if (!imageSearchStatus) return;
        imageSearchStatus.textContent = message;
        imageSearchStatus.classList.remove('text-secondary', 'text-success', 'text-danger', 'text-warning');
        if (type === 'success') imageSearchStatus.classList.add('text-success');
        else if (type === 'danger') imageSearchStatus.classList.add('text-danger');
        else if (type === 'warning') imageSearchStatus.classList.add('text-warning');
        else imageSearchStatus.classList.add('text-secondary');
    };

    searchImageInput.addEventListener('change', () => {
        const files = Array.from(searchImageInput.files || []);
        if (!files.length) {
            setStatus('Upload an image to match listings visually.');
            return;
        }
        const names = files.map(file => file.name).slice(0, 2);
        const suffix = files.length > 2 ? ` (+${files.length - 2} more)` : '';
        setStatus(`Selected: ${names.join(', ')}${suffix}`);
    });

    searchByImageBtn.addEventListener('click', async () => {
        const files = Array.from(searchImageInput.files || []);
        if (!files.length) {
            setStatus('Please select at least one image before searching.', 'warning');
            showNotification('Please select at least one image first.', 'warning');
            return;
        }

        const formData = new FormData();
        files.forEach(file => formData.append('search_image', file));

        searchByImageBtn.disabled = true;
        const previousButtonText = searchByImageBtn.innerHTML;
        searchByImageBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Analyzing...';
        setStatus(`Analyzing ${files.length} image(s) and finding visual matches...`);

        try {
            const response = await fetch('/api/search-by-image/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
                body: formData,
            });

            // When not logged in, Django may redirect to login page.
            if (response.redirected && response.url) {
                window.location.href = response.url;
                return;
            }

            const data = await response.json().catch(() => null);
            if (!response.ok || !data) {
                throw new Error(data?.message || `Image search failed (${response.status})`);
            }

            if (data.success) {
                const tags = Array.isArray(data.amenity_tags) ? data.amenity_tags : (Array.isArray(data.detected_features) ? data.detected_features : []);
                const detail = tags.length ? ` Tags: ${tags.slice(0, 8).join(', ')}` : '';
                setStatus(`${data.message || 'Image search complete.'}${detail}`, 'success');
                showNotification(data.message || 'Image search complete.', 'success');
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            } else {
                const detected = Array.isArray(data.detected_features) ? data.detected_features : [];
                const detail = detected.length ? ` Detected: ${detected.slice(0, 5).join(', ')}` : '';
                setStatus(`${data.message || 'Unable to complete image search.'}${detail}`, 'danger');
                showNotification(data.message || 'Unable to complete image search.', 'danger');
            }
        } catch (error) {
            console.error('Image search error:', error);
            const errorMessage = error?.message || 'Unable to process image search right now.';
            setStatus(errorMessage, 'danger');
            showNotification(errorMessage, 'danger');
        } finally {
            searchByImageBtn.disabled = false;
            searchByImageBtn.innerHTML = previousButtonText;
        }
    });
}

// ============================================
// Favorite Functionality
// ============================================

function toggleFavorite(e) {
    e.preventDefault();
    const btn = e.target.closest('.btn-favorite, .btn-favorite-side');
    const propertyId = btn.dataset.propertyId;

    if (!propertyId) {
        showNotification('Please login to add favorites', 'warning');
        window.location.href = '/accounts/login/';
        return;
    }

    const url = `/favorites/toggle/${propertyId}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    })
        .then(response => {
            if (response.status === 401) {
                showNotification('Please login to add favorites', 'warning');
                window.location.href = '/accounts/login/';
                return Promise.reject('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                btn.classList.toggle('active');
                const icon = '<i class="fas fa-heart"></i> ';
                btn.innerHTML = data.is_favorite ? `${icon}Saved` : `${icon}Save`;
                showNotification(data.message, 'success');
            } else if (data) {
                showNotification(data.message, 'danger');
            }
        })
        .catch(error => {
            if (error !== 'Unauthorized') {
                console.error('Error:', error);
                showNotification('Error adding to favorites', 'danger');
            }
        });
}

// ============================================
// Search & Filter
// ============================================

function handleSearch(e) {
    const minPrice = document.querySelector('input[name="min_price"]')?.value;
    const maxPrice = document.querySelector('input[name="max_price"]')?.value;

    // Basic validation
    if (minPrice && maxPrice && parseInt(minPrice) > parseInt(maxPrice)) {
        e.preventDefault();
        showNotification('Minimum price cannot be greater than maximum price', 'warning');
    }
}

function updatePriceDisplay(e) {
    const slider = e.target;
    const value = slider.value;
    const display = document.querySelector(`[data-price-display="${slider.id}"]`);

    if (display) {
        display.textContent = `â‚¹${parseInt(value).toLocaleString()}`;
    }
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'info') {
    const alertClass = `alert alert-${type}`;
    const alertHTML = `
        <div class="${alertClass}" role="alert">
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            ${message}
        </div>
    `;

    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    alertContainer.innerHTML = alertHTML;

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '80px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// ============================================
// Tooltips & Popovers
// ============================================

function initializeTooltips() {
    if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) {
        return;
    }

    // Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeBootstrapFallbacks() {
    const isBootstrapReady = typeof bootstrap !== 'undefined';
    if (isBootstrapReady) {
        return;
    }

    // Navbar collapse fallback when CDN/bootstrap JS is unavailable.
    const navbarToggle = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('#navbarNav');
    if (navbarToggle && navbarCollapse) {
        navbarToggle.addEventListener('click', function () {
            const isOpen = navbarCollapse.classList.contains('show');
            navbarCollapse.classList.toggle('show', !isOpen);
            navbarToggle.setAttribute('aria-expanded', String(!isOpen));
        });
    }

    // Basic dropdown fallback for account menu.
    const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function (event) {
            event.preventDefault();
            const menu = toggle.nextElementSibling;
            if (!menu || !menu.classList.contains('dropdown-menu')) return;
            menu.classList.toggle('show');
        });
    });

    document.addEventListener('click', function (event) {
        if (event.target.closest('[data-bs-toggle="dropdown"]')) return;
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => menu.classList.remove('show'));
    });
}

function initializeMagicalFloaters() {
    // Magical effects are handled via CSS animations
    // Add any additional JS-based magical effects here if needed
}

// NOTE: initializeAiConcierge is defined later in this file.

function scrollToContact() {
    const target = document.getElementById('contactSection');
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function toggleComparison(e) {
    e.preventDefault();
    const button = e.currentTarget;
    const propertyId = button.dataset.propertyId;
    const compareUrl = button.dataset.compareUrl || `/add-to-comparison/${propertyId}/`;
    if (!propertyId || !compareUrl) {
        showNotification('Unable to compare this property right now.', 'warning');
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');

    fetch(compareUrl, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    })
        .then(async response => {
            const contentType = response.headers.get('content-type') || '';
            let data = null;
            if (contentType.includes('application/json')) {
                data = await response.json().catch(() => null);
            }
            if (!response.ok) {
                const message = data?.message || `Unable to update comparison list. (${response.status})`;
                showNotification(message, 'danger');
                return null;
            }
            if (!data) {
                showNotification('Unable to update comparison list. Invalid server response.', 'danger');
                return null;
            }
            return data;
        })
        .then(data => {
            if (!data) return;
            if (!data.success) {
                showNotification(data.message || 'Unable to update comparison list.', 'danger');
                return;
            }

            button.classList.toggle('active', data.action === 'added');
            button.innerHTML = data.action === 'added'
                ? '<i class="fas fa-balance-scale"></i> Added to Compare'
                : '<i class="fas fa-balance-scale"></i> Compare Property';

            showNotification(data.message, 'success');

            if (data.count >= 2) {
                setTimeout(() => {
                    window.location.href = '/comparison-list/';
                }, 750);
            }
        })
        .catch(error => {
            console.error('Comparison error:', error);
            showNotification('Unable to update comparison list.', 'danger');
        });
}

// ============================================
// Image Gallery
// ============================================

function initializeGallery(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const thumbnails = container.querySelectorAll('.gallery-item img');
    const mainImage = container.querySelector('.property-detail-hero img');

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function () {
            mainImage.src = this.src;
            mainImage.alt = this.alt;

            // Update active state
            thumbnails.forEach(img => img.parentElement.classList.remove('active'));
            this.parentElement.classList.add('active');
        });
    });
}

// ============================================
// Utility Functions
// ============================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
    }).format(value);
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

// ============================================
// Lazy Loading Images
// ============================================

function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const images = document.querySelectorAll('img[data-src]');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => observer.observe(img));
    }
}

// ============================================
// Form Validation
// ============================================

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// ============================================
// Mobile Optimizations
// ============================================

function initializeMobileOptimizations() {
    // Prevent double-tap zoom on buttons and interactive elements
    const interactiveElements = document.querySelectorAll('button, .btn, .nav-link, .dropdown-item, .ai-concierge-toggle, .ai-quick-chip');
    
    interactiveElements.forEach(element => {
        let lastTouchEnd = 0;
        element.addEventListener('touchend', function(event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    });

    // Prevent zoom on input focus for iOS
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            // This helps prevent zoom on iOS when focusing inputs
            this.setAttribute('autocomplete', 'off');
        });
    });

    // Improve scrolling performance on mobile
    if ('ontouchstart' in window) {
        document.addEventListener('touchstart', function() {}, { passive: true });
        document.addEventListener('touchmove', function() {}, { passive: true });
    }
}

// ============================================
// AI Concierge (Chatbot)
// ============================================

function initializeAiConcierge() {
    const widget = document.getElementById('aiConciergeWidget');
    if (!widget) return;

    const toggle = document.getElementById('aiConciergeToggle');
    const panel = document.getElementById('aiConciergePanel');
    const closeBtn = document.getElementById('aiConciergeClose');
    const newChatBtn = document.getElementById('aiConciergeNewChat');
    const header = panel ? panel.querySelector('.ai-concierge-header') : null;
    const titleNode = panel ? panel.querySelector('.luxe-chat-title') : null;
    const subTitleNode = panel ? panel.querySelector('.luxe-chat-sub') : null;
    const messages = document.getElementById('aiConciergeMessages');
    const form = document.getElementById('aiConciergeForm');
    const input = document.getElementById('aiConciergeInput');
    const sendBtn = document.getElementById('aiConciergeSend');
    const quickActions = document.getElementById('aiConciergeQuickActions');
    const useMemoryToggle = document.getElementById('aiUseMemoryToggle');

    const endpoint = widget.dataset.chatEndpoint;
    const TRANSCRIPT_KEY = 'luxeAiTranscript';
    const USE_MEMORY_KEY = 'luxeAiUseMemory';
    const TRANSCRIPT_LIMIT = 50;

    let useMemory = false;  // Memory always disabled - always start fresh
    let requestInFlight = false;
    let lead = {
        intent: '',
        name: '',
        contact: '',
        budget: '',
        city: '',
        property_type: '',
        bhk: '',
    };

    const setUseMemory = (value, persist = false) => {
        useMemory = !!value;
        if (useMemoryToggle) {
            useMemoryToggle.checked = useMemory;
        }
        if (persist) {
            try {
                localStorage.setItem(USE_MEMORY_KEY, useMemory ? '1' : '0');
            } catch (error) {
                console.warn('Could not persist memory preference:', error);
            }
        }
    };

    const captureLeadData = (message) => {
        // Extract lead information from user messages
        const lower = message.toLowerCase();
        
        // Extract email
        const emailMatch = message.match(/[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}/);
        if (emailMatch) lead.contact = emailMatch[0];
        
        // Extract phone
        const phoneMatch = message.match(/(?:\+91|0)?\s*([1-9]\d{9})\b/);
        if (phoneMatch) lead.contact = phoneMatch[1];
        
        // Extract name
        const nameMatch = message.match(/(?:my name is|i am|i'm)\s+([A-Za-z][A-Za-z ]{1,40})/i);
        if (nameMatch) lead.name = nameMatch[1].trim().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
        
        // Extract budget
        const budgetMatch = message.match(/(\d+(?:\.\d+)?)\s*(lakh|lac|l\b|crore|cr\b|k\b)?/i);
        if (budgetMatch) lead.budget = budgetMatch[0].trim();
        
        // Extract city
        const cityMatch = message.match(/(?:in|at|near)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+(?:for|under|budget|price)|\b|$)/i);
        if (cityMatch) lead.city = cityMatch[1].trim().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
        
        // Extract BHK
        const bhkMatch = message.match(/(\d+)\s*(?:bhk|bedroom|bedrooms|beds?)/i);
        if (bhkMatch) lead.bhk = `${bhkMatch[1]} BHK`;
        
        // Extract property type
        const typeMatch = message.match(/\b(apartment|flat|villa|plot|house|studio|penthouse|commercial|office|shop|farmland)\b/i);
        if (typeMatch) {
            const rawType = typeMatch[1].toLowerCase();
            lead.property_type = rawType === 'flat' ? 'apartment' : rawType;
        }
    };

    const syncLeadFromBackend = (data) => {
        if (data.lead) {
            lead = { ...lead, ...data.lead };
        }
    };

    const localFallbackReply = (message) => {
        const fallbacks = [
            "I'm here to help you find your perfect property. What are you looking for?",
            "I'd be happy to assist with your property search. Could you tell me more about what you're looking for?",
            "Let me help you discover great properties. What's your budget and preferred location?",
        ];
        return fallbacks[Math.floor(Math.random() * fallbacks.length)];
    };

    // Render the panel at document root level so it never gets clipped by
    // hero/section stacking or overflow contexts.
    if (panel.parentElement !== document.body) {
        document.body.appendChild(panel);
    }
    panel.classList.add('ai-concierge-portal');

    const resetPanelInlineStyles = () => {
        panel.style.position = '';
        panel.style.right = '';
        panel.style.left = '';
        panel.style.width = '';
        panel.style.bottom = '';
        panel.style.maxHeight = '';
        panel.style.zIndex = '';
        panel.style.display = '';
        panel.style.opacity = '';
        panel.style.visibility = '';
        panel.style.pointerEvents = '';
        panel.style.transform = '';
    };

    const enforceHeaderVisibility = () => {
        if (!header) return;
        header.style.setProperty('display', 'flex', 'important');
        header.style.setProperty('align-items', 'center', 'important');
        header.style.setProperty('justify-content', 'space-between', 'important');
        header.style.setProperty('visibility', 'visible', 'important');
        header.style.setProperty('opacity', '1', 'important');
        header.style.setProperty('min-height', '74px', 'important');
        header.style.setProperty('padding', '1rem 1.2rem', 'important');
        header.style.setProperty('z-index', '4', 'important');
        header.style.setProperty('position', 'sticky', 'important');
        header.style.setProperty('top', '0', 'important');
        if (titleNode) {
            titleNode.style.setProperty('display', 'block', 'important');
            titleNode.style.setProperty('color', '#ffffff', 'important');
            titleNode.style.setProperty('visibility', 'visible', 'important');
            titleNode.style.setProperty('opacity', '1', 'important');
        }
        if (subTitleNode) {
            subTitleNode.style.setProperty('display', 'block', 'important');
            subTitleNode.style.setProperty('color', 'rgba(255, 255, 255, 0.92)', 'important');
            subTitleNode.style.setProperty('visibility', 'visible', 'important');
            subTitleNode.style.setProperty('opacity', '1', 'important');
        }
        if (closeBtn) {
            closeBtn.style.setProperty('display', 'inline-flex', 'important');
            closeBtn.style.setProperty('align-items', 'center', 'important');
            closeBtn.style.setProperty('justify-content', 'center', 'important');
            closeBtn.style.setProperty('visibility', 'visible', 'important');
            closeBtn.style.setProperty('opacity', '1', 'important');
            closeBtn.style.setProperty('color', '#ffffff', 'important');
            closeBtn.style.setProperty('min-width', '42px', 'important');
            closeBtn.style.setProperty('min-height', '42px', 'important');
            closeBtn.style.setProperty('z-index', '5', 'important');
        }
    };

    const adjustPanelPosition = () => {
        resetPanelInlineStyles();
        if (!panel.classList.contains('open')) return;

        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const isMobileViewport = viewportWidth <= 767;

        // Always pin the panel to the viewport so hero/layout stacking
        // contexts cannot hide it behind section layers.
        panel.style.position = 'fixed';
        panel.style.zIndex = '9999';

        if (isMobileViewport) {
            panel.style.left = '0.5rem';
            panel.style.right = '0.5rem';
            panel.style.width = 'auto';
            panel.style.bottom = 'calc(96px + 0.75rem)';
            panel.style.maxHeight = `${Math.max(320, Math.floor(viewportHeight * 0.68))}px`;
            return;
        }

        panel.style.right = '0.75rem';
        panel.style.left = 'auto';
        panel.style.width = `min(430px, calc(100vw - 2rem))`;
        panel.style.bottom = 'calc(96px + 0.75rem)';
        panel.style.maxHeight = `${Math.max(320, Math.floor(viewportHeight * 0.68))}px`;
    };

    const persistTranscript = () => {
        if (!useMemory) return;
        try {
            const bubbles = Array.from(messages.querySelectorAll('.ai-msg[data-sender]'));
            const transcript = bubbles
                .map((node) => ({
                    sender: node.dataset.sender || 'bot',
                    text: (node.querySelector('.ai-msg-text')?.textContent || node.textContent || '').trim(),
                    muted: node.classList.contains('ai-msg-muted'),
                    ts: node.dataset.ts || new Date().toISOString(),
                }))
                .filter((item) => item.text);
            localStorage.setItem(TRANSCRIPT_KEY, JSON.stringify(transcript.slice(-TRANSCRIPT_LIMIT)));
        } catch (error) {
            console.warn('Could not persist AI transcript:', error);
        }
    };

    const addMessage = (text, sender = 'bot', muted = false, timestampIso = null) => {
        const bubble = document.createElement('div');
        bubble.className = `ai-msg ${sender === 'user' ? 'ai-msg-user' : 'ai-msg-bot'}${muted ? ' ai-msg-muted' : ''}`;
        bubble.dataset.sender = sender;
        const ts = timestampIso || new Date().toISOString();
        bubble.dataset.ts = ts;
        const tsDate = new Date(ts);
        const displayTime = Number.isNaN(tsDate.getTime())
            ? new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
            : tsDate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        const content = document.createElement('div');
        content.className = 'ai-msg-text';
        content.textContent = text;
        const stamp = document.createElement('span');
        stamp.className = 'ai-msg-time';
        stamp.textContent = displayTime;
        bubble.appendChild(content);
        bubble.appendChild(stamp);

        const prev = messages.lastElementChild;
        if (prev && prev.classList.contains('ai-msg') && prev.dataset.sender === sender) {
            bubble.classList.add('ai-msg-grouped');
        }

        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
        persistTranscript();
    };

    const addTyping = () => {
        const typing = document.createElement('div');
        typing.className = 'ai-msg ai-msg-bot ai-typing';
        typing.setAttribute('aria-live', 'polite');
        typing.innerHTML = `
            <div class="ai-typing-dots">
                <span></span><span></span><span></span>
            </div>
            <span class="ai-msg-time">${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
        `;
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
        return typing;
    };

    const restoreTranscript = () => {
        if (!useMemory) return false;
        try {
            const raw = localStorage.getItem(TRANSCRIPT_KEY);
            if (!raw) return false;
            const items = JSON.parse(raw);
            if (!Array.isArray(items) || !items.length) return false;
            messages.innerHTML = '';
            items.forEach((item) => {
                if (!item || typeof item.text !== 'string') return;
                addMessage(item.text, item.sender === 'user' ? 'user' : 'bot', Boolean(item.muted), item.ts || null);
            });
            return true;
        } catch (error) {
            console.warn('Could not restore AI transcript:', error);
            return false;
        }
    };

    // Clear any stored memory on init - always start fresh
    try {
        localStorage.removeItem(TRANSCRIPT_KEY);
        localStorage.removeItem(USE_MEMORY_KEY);
    } catch (error) {
        console.warn('Could not clear AI transcript on init:', error);
    }

    const sendMessage = async (seedMessage) => {
        const message = (seedMessage || input.value || '').trim();
        if (!message || requestInFlight) return;
        requestInFlight = true;
        if (sendBtn) sendBtn.disabled = true;
        if (input) input.disabled = true;
        addMessage(message, 'user');
        input.value = '';
        captureLeadData(message);

        const typing = addTyping();
        let reply = '';

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message,
                    intent: lead.intent,
                    lead_name: lead.name,
                    lead_contact: lead.contact,
                    lead_budget: lead.budget,
                    lead_city: lead.city,
                    lead_property_type: lead.property_type,
                    lead_bhk: lead.bhk,
                    use_memory: useMemory,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('AI concierge failed:', response.status, errorData);
                reply = (typeof errorData.response === 'string' && errorData.response.trim())
                    ? errorData.response.trim()
                    : localFallbackReply(message);
            } else {
                const data = await response.json();
                syncLeadFromBackend(data);
                reply = data.response || localFallbackReply(message);
                if (data.requires_human) {
                    addMessage(`I am routing this to a human agent. Reason: ${data.handoff_reason || 'Requested by user.'}`, 'bot', true);
                }
            }
        } catch (error) {
            console.error('AI concierge error:', error);
            reply = localFallbackReply(message);
        } finally {
            typing.remove();
            requestInFlight = false;
            if (sendBtn) sendBtn.disabled = false;
            if (input) {
                input.disabled = false;
                input.focus();
            }
        }

        addMessage(reply, 'bot');
    };

    const nimPanel = () => {
        panel.classList.add('open');
        toggle.classList.add('active');
        // Clear transcript every time panel opens to ensure fresh chat
        try {
            localStorage.removeItem(TRANSCRIPT_KEY);
        } catch (error) {
            console.warn('Could not clear AI transcript:', error);
        }
        // Force visible state inline to defeat any conflicting CSS layer.
        panel.style.setProperty('display', 'grid', 'important');
        panel.style.setProperty('grid-template-rows', 'auto auto 1fr auto', 'important');
        panel.style.setProperty('opacity', '1', 'important');
        panel.style.setProperty('visibility', 'visible', 'important');
        panel.style.setProperty('pointer-events', 'auto', 'important');
        panel.style.setProperty('transform', 'translateY(0)', 'important');
        panel.style.setProperty('z-index', '2147483647', 'important');
        panel.style.setProperty('overflow', 'hidden', 'important');
        enforceHeaderVisibility();
        setTimeout(() => input.focus(), 180);
        adjustPanelPosition();
    };

    const closeAiPanel = () => {
        panel.classList.remove('open');
        toggle.classList.remove('active');
        resetPanelInlineStyles();
    };

    const toggleAiPanel = () => {
        if (panel.classList.contains('open')) {
            closeAiPanel();
        } else {
            nimPanel();
        }
    };

    const resetChat = () => {
        // Clear all messages from the UI
        messages.innerHTML = '';
        
        // Clear transcript from localStorage (but respect memory preference)
        try {
            localStorage.removeItem(TRANSCRIPT_KEY);
        } catch (error) {
            console.warn('Could not clear AI transcript:', error);
        }
        
        // Reset lead data
        lead = {
            intent: '',
            name: '',
            contact: '',
            budget: '',
            city: '',
            property_type: '',
            bhk: '',
        };
        
        // Reset input and button state
        input.value = '';
        input.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        requestInFlight = false;
        
        // Show welcome message
        addMessage("Hello. Ask about properties, budgets, or site visits.", 'bot');
        
        // Focus input
        setTimeout(() => input.focus(), 100);
    };

    // Prevent touch+click double firing on mobile/emulation.
    const bindTap = (element, handler) => {
        let lastTouchAt = 0;
        element.addEventListener('touchstart', (e) => {
            lastTouchAt = Date.now();
        });
        element.addEventListener('click', (e) => {
            const now = Date.now();
            if (now - lastTouchAt > 300) {
                handler(e);
            }
        });
    };

    // Event listeners
    if (toggle) bindTap(toggle, toggleAiPanel);
    if (closeBtn) bindTap(closeBtn, closeAiPanel);
    if (newChatBtn) bindTap(newChatBtn, resetChat);

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            sendMessage();
        });
    }

    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (quickActions) {
        quickActions.addEventListener('click', (e) => {
            const chip = e.target.closest('.ai-quick-chip');
            if (chip) {
                const message = chip.dataset.chip;
                if (message) {
                    sendMessage(message);
                }
            }
        });
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        if (panel.classList.contains('open')) {
            enforceHeaderVisibility();
            adjustPanelPosition();
        }
    });

    // Handle escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && panel.classList.contains('open')) {
            closeAiPanel();
        }
    });

    if (!useMemory) {
        try {
            localStorage.removeItem(TRANSCRIPT_KEY);
        } catch (error) {
            console.warn('Could not clear AI transcript:', error);
        }
    }
    const hasTranscript = restoreTranscript();

    // Auto-open on first visit or show welcome message
    const hasVisited = localStorage.getItem('luxeAiVisited');
    if (!hasVisited && !hasTranscript) {
        localStorage.setItem('luxeAiVisited', 'true');
        setTimeout(() => {
            addMessage("👋 Hi! I'm Luxe AI Concierge. I handle property inquiries, qualify leads, schedule appointments, and provide immediate customer support 24/7. Are you looking to buy, rent, or invest today?", 'bot');
        }, 2000);
    } else if (!hasTranscript) {
        addMessage("Hello. Ask about properties, budgets, or site visits.", 'bot');
    }
    enforceHeaderVisibility();
}

