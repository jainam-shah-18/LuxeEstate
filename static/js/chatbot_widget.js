/**
 * LuxeEstate Intelligent Chatbot Widget
 * Embed this in your website for 24/7 customer support
 */

class LuxeEstateChatbot {
  constructor(options = {}) {
    this.apiBaseUrl = options.apiBaseUrl || '/api/chatbot';
    this.propertyId = options.propertyId || null;
    this.visitorName = options.visitorName || null;
    this.visitorEmail = options.visitorEmail || null;
    this.visitorPhone = options.visitorPhone || null;
    
    this.conversationId = null;
    this.isOpen = false;
    this.isLoading = false;
    
    this.init();
  }

  init() {
    this.createWidgetHTML();
    this.attachEventListeners();
    this.logWelcomeMessage();
  }

  createWidgetHTML() {
    const widgetHTML = `
      <div id="luxe-chatbot-widget" class="chatbot-widget">
        <!-- Floating Button -->
        <div id="chatbot-toggle" class="chatbot-toggle" title="Chat with our AI Assistant">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="notification-badge" id="notification-badge">1</span>
        </div>

        <!-- Chat Window -->
        <div id="chatbot-window" class="chatbot-window hidden">
          <!-- Header -->
          <div class="chatbot-header">
            <div class="chatbot-header-content">
              <h3>LuxeEstate Assistant 🏠</h3>
              <p>24/7 Support</p>
            </div>
            <button id="chatbot-close" class="chatbot-close-btn" aria-label="Close chat">×</button>
          </div>

          <!-- Messages Container -->
          <div id="chatbot-messages" class="chatbot-messages">
            <!-- Messages will be added here -->
          </div>

          <!-- Input Area -->
          <div class="chatbot-input-area">
            <input
              id="chatbot-input"
              type="text"
              placeholder="Type your message..."
              autocomplete="off"
            />
            <button id="chatbot-send" class="chatbot-send-btn" aria-label="Send message">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </div>
    `;

    // Inject into body
    const container = document.createElement('div');
    container.innerHTML = widgetHTML;
    document.body.appendChild(container);
    
    // Inject CSS
    this.injectStyles();
  }

  injectStyles() {
    const styles = `
      #luxe-chatbot-widget {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
      }

      /* Floating Button */
      .chatbot-toggle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        position: relative;
      }

      .chatbot-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
      }

      .chatbot-toggle:active {
        transform: scale(0.95);
      }

      .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #ff4757;
        color: white;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        opacity: 0;
        transition: opacity 0.3s;
      }

      .notification-badge.show {
        opacity: 1;
      }

      /* Chat Window */
      .chatbot-window {
        position: absolute;
        bottom: 80px;
        right: 0;
        width: 400px;
        height: 600px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 40px rgba(0, 0, 0, 0.16);
        display: flex;
        flex-direction: column;
        transition: opacity 0.3s, transform 0.3s;
      }

      .chatbot-window.hidden {
        opacity: 0;
        transform: scale(0.95) translateY(20px);
        pointer-events: none;
      }

      /* Header */
      .chatbot-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: start;
      }

      .chatbot-header-content h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .chatbot-header-content p {
        margin: 4px 0 0 0;
        font-size: 12px;
        opacity: 0.9;
      }

      .chatbot-close-btn {
        background: none;
        border: none;
        color: white;
        font-size: 28px;
        cursor: pointer;
        padding: 0;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .chatbot-close-btn:hover {
        opacity: 0.8;
      }

      /* Messages */
      .chatbot-messages {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        background: #f8f9fa;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .chatbot-message {
        display: flex;
        animation: slideIn 0.3s ease;
        max-width: 85%;
      }

      .chatbot-message.user {
        justify-content: flex-end;
      }

      .chatbot-message.bot {
        justify-content: flex-start;
      }

      .message-content {
        padding: 12px 16px;
        border-radius: 12px;
        word-wrap: break-word;
        line-height: 1.5;
        font-size: 14px;
      }

      .message-content.user {
        background: #667eea;
        color: white;
        border-radius: 18px 18px 4px 18px;
      }

      .message-content.bot {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-radius: 18px 18px 18px 4px;
      }

      .message-loading {
        display: flex;
        gap: 6px;
        padding: 12px 16px;
      }

      .loading-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: bounce 1.4s infinite;
      }

      .loading-dot:nth-child(2) {
        animation-delay: 0.2s;
      }

      .loading-dot:nth-child(3) {
        animation-delay: 0.4s;
      }

      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes bounce {
        0%, 80%, 100% {
          transform: translateY(0);
        }
        40% {
          transform: translateY(-10px);
        }
      }

      /* Input Area */
      .chatbot-input-area {
        display: flex;
        gap: 8px;
        padding: 12px 16px;
        border-top: 1px solid #e0e0e0;
        background: white;
        border-radius: 0 0 12px 12px;
      }

      #chatbot-input {
        flex: 1;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        padding: 10px 16px;
        font-size: 14px;
        outline: none;
        transition: border-color 0.3s;
      }

      #chatbot-input:focus {
        border-color: #667eea;
      }

      .chatbot-send-btn {
        background: #667eea;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: background 0.3s;
      }

      .chatbot-send-btn:hover {
        background: #764ba2;
      }

      .chatbot-send-btn:disabled {
        background: #ccc;
        cursor: not-allowed;
      }

      /* Responsive */
      @media (max-width: 480px) {
        .chatbot-window {
          width: calc(100vw - 40px);
          height: 70vh;
          max-height: 600px;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        * {
          animation: none !important;
          transition: none !important;
        }
      }
    `;

    const styleTag = document.createElement('style');
    styleTag.textContent = styles;
    document.head.appendChild(styleTag);
  }

  attachEventListeners() {
    document.getElementById('chatbot-toggle').addEventListener('click', () => this.toggleChat());
    document.getElementById('chatbot-close').addEventListener('click', () => this.closeChat());
    document.getElementById('chatbot-send').addEventListener('click', () => this.sendMessage());

    document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }

  toggleChat() {
    if (this.isOpen) {
      this.closeChat();
    } else {
      this.openChat();
    }
  }

  openChat() {
    const window = document.getElementById('chatbot-window');
    window.classList.remove('hidden');
    this.isOpen = true;
    
    // Hide notification badge
    const badge = document.getElementById('notification-badge');
    badge?.classList.remove('show');
    
    // Start conversation if not already started
    if (!this.conversationId) {
      this.startConversation();
    }

    // Focus input
    setTimeout(() => {
      document.getElementById('chatbot-input').focus();
    }, 300);
  }

  closeChat() {
    const window = document.getElementById('chatbot-window');
    window.classList.add('hidden');
    this.isOpen = false;
  }

  logWelcomeMessage() {
    const messagesContainer = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chatbot-message bot';
    messageDiv.innerHTML = `<div class="message-content bot">👋 Hi there! Click the chat button below to get started.</div>`;
    messagesContainer.appendChild(messageDiv);
  }

  async startConversation() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/conversations/start_conversation/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          visitor_name: this.visitorName,
          visitor_email: this.visitorEmail,
          visitor_phone: this.visitorPhone,
          property_id: this.propertyId,
        }),
      });

      const data = await response.json();
      this.conversationId = data.id;
      this.addMessage(data.messages[0]?.message || 'Hello! How can I help?', 'bot');
    } catch (error) {
      console.error('Failed to start conversation:', error);
      this.addMessage('Sorry, I encountered an error. Please refresh and try again.', 'bot');
    }
  }

  async sendMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();

    if (!message || this.isLoading) return;

    // Add user message
    this.addMessage(message, 'user');
    input.value = '';

    // Show loading indicator
    this.showLoadingIndicator();
    this.isLoading = true;

    try {
      const response = await fetch(
        `${this.apiBaseUrl}/conversations/${this.conversationId}/send_message/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message }),
        }
      );

      const data = await response.json();

      // Remove loading indicator
      this.removeLoadingIndicator();

      // Add bot response
      this.addMessage(data.bot_response, 'bot');

      // Show notification if lead qualified
      if (data.is_qualified) {
        console.log('Lead qualified! Consider scheduling a tour.');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      this.removeLoadingIndicator();
      this.addMessage('Sorry, I had trouble processing that. Please try again.', 'bot');
    } finally {
      this.isLoading = false;
      document.getElementById('chatbot-input').focus();
    }
  }

  addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${sender}`;
    messageDiv.innerHTML = `<div class="message-content ${sender}">${this.escapeHtml(text)}</div>`;
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  showLoadingIndicator() {
    const messagesContainer = document.getElementById('chatbot-messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chatbot-message bot';
    loadingDiv.id = 'loading-indicator';
    loadingDiv.innerHTML = `
      <div class="message-loading">
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
      </div>
    `;
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  removeLoadingIndicator() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
      loading.remove();
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showNotification() {
    const badge = document.getElementById('notification-badge');
    if (badge && !this.isOpen) {
      badge.classList.add('show');
    }
  }
}

// Auto-initialize if data attributes present
document.addEventListener('DOMContentLoaded', () => {
  const script = document.currentScript;
  if (script?.dataset.autoInit === 'true') {
    window.luxeEstateChatbot = new LuxeEstateChatbot({
      apiBaseUrl: script?.dataset.apiUrl || '/api/chatbot',
      propertyId: script?.dataset.propertyId || null,
    });
  }
});
