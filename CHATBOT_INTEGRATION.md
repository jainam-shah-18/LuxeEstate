# LuxeEstate AI Chatbot - Quick Integration Guide

## 📌 Quick Start

Add this to your `properties/views.py` to enable the chatbot:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from properties.chatbot_service import chatbot
import json

@require_http_methods(["POST"])
def chatbot_message(request):
    """
    Handle chatbot messages with real-time property responses.
    
    POST body:
    {
        "message": "I want to buy a 2BHK in Pune",
        "session_id": "user_session_id" (optional)
    }
    
    Returns:
    {
        "message": "Response text",
        "intent": "buy|rent|invest|appointment|out_of_scope|...",
        "lead": {...},
        "appointment": {...},
        "qualification_stage": "cold|warm|hot",
        "agent_assigned": "agent_name|null",
        "out_of_scope": false,
        "qualified_lead": false,
        ...
    }
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message required'}, status=400)
        
        # Get or create conversation state
        session_state = request.session.get('chatbot_state', {})
        
        # Process message with chatbot
        result = chatbot.process_message(user_message, session_state)
        
        # Save state in session
        request.session['chatbot_state'] = {
            'lead': result['lead'],
            'chat_history': result['chat_history'][-20:],  # Keep last 20 messages
            'search_criteria': result['search_criteria'],
            'appointment': result['appointment'],
            'asked_fields': result['asked_fields'],
        }
        
        # Return response
        return JsonResponse(result, safe=False)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chatbot_page(request):
    """Render chatbot page with session history"""
    context = {
        'chat_history': request.session.get('chatbot_state', {}).get('chat_history', []),
        'lead_info': request.session.get('chatbot_state', {}).get('lead', {}),
    }
    return render(request, 'properties/chatbot.html', context)
```

## 🔗 Add to URLs

```python
# properties/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ... existing patterns ...
    path('api/chatbot/', views.chatbot_message, name='chatbot_message'),
    path('chatbot/', views.chatbot_page, name='chatbot_page'),
]
```

## 🎨 Frontend Integration

### HTML Template

```html
<!-- templates/properties/chatbot.html -->
<div class="chatbot-container">
    <div class="chat-messages" id="chatMessages">
        <!-- Messages appear here -->
    </div>
    
    <div class="chat-input-area">
        <input 
            type="text" 
            id="userInput" 
            placeholder="Ask me about properties in Pune..." 
            maxlength="1000"
        />
        <button onclick="sendMessage()">Send</button>
    </div>
</div>

<script>
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';
    
    try {
        // Send to backend
        const response = await fetch('/api/chatbot/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message})
        });
        
        if (!response.ok) throw new Error('API error');
        const data = await response.json();
        
        // Add bot response
        addMessageToChat(data.message, 'bot');
        
        // Show lead info if available
        if (data.qualified_lead) {
            showLeadInfo(data.lead);
        }
        
        // Show appointment confirmation if booked
        if (data.appointment.confirmed) {
            showAppointmentAlert(data.appointment);
        }
        
        // Highlight if out of scope
        if (data.out_of_scope) {
            console.warn('Out of scope query detected');
        }
        
    } catch (error) {
        addMessageToChat('Error: Unable to process message', 'error');
        console.error(error);
    }
}

function addMessageToChat(text, sender) {
    const messagesDiv = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${sender}`;
    msgDiv.textContent = text;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showLeadInfo(lead) {
    const leadText = Object.entries(lead)
        .filter(([_, v]) => v)
        .map(([k, v]) => `${k}: ${v}`)
        .join(' | ');
    
    console.log('Lead Profile:', leadText);
}

function showAppointmentAlert(appointment) {
    alert(`Appointment scheduled for ${appointment.preferred_datetime}\n` +
          `Contact: ${appointment.property_hint}`);
}
</script>

<style>
.chatbot-container {
    max-width: 600px;
    border: 1px solid #ddd;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    height: 600px;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: #f9f9f9;
}

.message {
    margin: 8px 0;
    padding: 8px 12px;
    border-radius: 4px;
    word-wrap: break-word;
}

.message-user {
    background: #007bff;
    color: white;
    margin-left: 40px;
}

.message-bot {
    background: #e9ecef;
    margin-right: 40px;
}

.message-error {
    background: #f8d7da;
    color: #721c24;
}

.chat-input-area {
    display: flex;
    padding: 12px;
    gap: 8px;
}

.chat-input-area input {
    flex: 1;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.chat-input-area button {
    padding: 8px 16px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.chat-input-area button:hover {
    background: #0056b3;
}
</style>
```

## 📊 Track Response Types

```python
# In your view or analytics
def get_chatbot_analytics(request):
    """Get chatbot interaction statistics"""
    from properties.models import Lead
    
    total_leads = Lead.objects.count()
    hot_leads = Lead.objects.filter(qualification_stage='hot').count()
    warm_leads = Lead.objects.filter(qualification_stage='warm').count()
    cold_leads = Lead.objects.filter(qualification_stage='cold').count()
    
    return JsonResponse({
        'total_conversations': total_leads,
        'hot_leads': hot_leads,
        'warm_leads': warm_leads,
        'cold_leads': cold_leads,
        'conversion_rate': f"{(hot_leads/total_leads*100) if total_leads > 0 else 0:.1f}%"
    })
```

## 🎯 Conversation Persistence

```python
# Store full conversation in session
request.session['chatbot_state'] = {
    'lead': result['lead'],                    # Current lead info
    'chat_history': result['chat_history'],    # Full message history
    'search_criteria': result['search_criteria'],  # Filters used
    'appointment': result['appointment'],      # Appointment data
    'asked_fields': result['asked_fields'],    # What we've asked
}

# Retrieve on next message
state = request.session.get('chatbot_state', {})
result = chatbot.process_message(new_message, state)
```

## 🔔 Handle Different Intent Types

```python
# In your response handler
if data['intent'] == 'greeting':
    # New conversation
    showWelcomeMessage()

elif data['intent'] == 'buy':
    # Property search request
    highlightPropertyResults()

elif data['intent'] == 'appointment':
    # Appointment scheduling
    showAppointmentForm()

elif data['intent'] == 'out_of_scope':
    # Off-topic query
    highlightScopeBoundary()
    suggestAlternativeTopic()

elif data['qualification_stage'] == 'hot':
    # Lead is qualified
    notifyAgent(data['agent_assigned'])
    enableAppointmentScheduling()

elif data['requires_human']:
    # User wants to talk to a human
    connectToAgent()
```

## 🚀 Real-Time Features

### Auto-Assign Agent to Hot Leads
```python
# Automatically happens in chatbot.process_message()
if result['qualification_stage'] == 'hot':
    agent = result['agent_assigned']
    # Send notification email/SMS to agent
    send_agent_notification(agent, result['lead'])
```

### Send Appointment Reminders
```python
# Call periodically (e.g., in a celery task)
from properties.chatbot_service import chatbot

# Send reminders for appointments in next 24 hours
chatbot.send_automated_followups()
```

### Track Lead Source
```python
# Add to Lead model
lead.source = 'chatbot'
lead.conversation_turns = len(chat_history)
lead.qualification_time = timezone.now() - lead.created_at
lead.save()
```

## 📱 Mobile-Friendly Layout

```html
<style>
@media (max-width: 768px) {
    .chatbot-container {
        max-width: 100%;
        height: 80vh;
    }
    
    .message-user {
        margin-left: 20px;
    }
    
    .message-bot {
        margin-right: 20px;
    }
}
</style>
```

## 🧪 Testing the Integration

```python
# tests/test_chatbot.py
from django.test import TestCase, Client
from properties.models import Property
import json

class ChatbotIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test properties
        Property.objects.create(
            title="Test Property",
            city="Pune",
            property_type="apartment",
            bedrooms=2,
            price=5000000
        )
    
    def test_property_search(self):
        response = self.client.post(
            '/api/chatbot/',
            json.dumps({'message': '2BHK in Pune'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['intent'], 'buy')
        self.assertIn('Pune', data['message'])
    
    def test_out_of_scope_handling(self):
        response = self.client.post(
            '/api/chatbot/',
            json.dumps({'message': 'What is the weather?'}),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['intent'], 'out_of_scope')
        self.assertIn('real estate', data['message'].lower())
    
    def test_lead_qualification(self):
        state = {'lead': {}, 'chat_history': []}
        
        # Step 1: Indicate intent
        response = self.client.post(
            '/api/chatbot/',
            json.dumps({'message': 'I want to buy'}),
            content_type='application/json'
        )
        self.assertEqual(response.json()['intent'], 'buy')
        
        # Step 2: Add more info
        response = self.client.post(
            '/api/chatbot/',
            json.dumps({'message': '2BHK in Pune under 50 lakh'}),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['qualification_stage'], 'cold')
        
        # Step 3: Provide contact
        response = self.client.post(
            '/api/chatbot/',
            json.dumps({'message': 'My name is Test, 9876543210'}),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['qualification_stage'], 'hot')
```

## 💾 Database Queries Generated

```python
# The chatbot automatically generates queries like:
Property.objects.filter(
    is_active=True,
    city__iexact='Pune',
    property_type='apartment',
    bedrooms=2,
    price__lte=5000000
).order_by('-is_featured', '-created_at')
```

## 🎁 Advanced Features

### Custom Intent Handler
```python
# Extend with your own intents
class CustomChatbot(LuxeChatbot):
    def detect_intent(self, message):
        intent = super().detect_intent(message)
        
        if 'rental yield' in message.lower():
            return 'investment_analysis'
        
        return intent
```

### Multi-Language Support
```python
# Add to chatbot_system_prompt.py
SYSTEM_PROMPTS = {
    'en': "You are LuxeEstate's AI real estate assistant...",
    'hi': "आप LuxeEstate के AI रियल एस्टेट सहायक हैं...",
}
```

---

**Your chatbot is now fully integrated and ready to handle 24/7 property inquiries!** 🚀
