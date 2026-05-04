# NVIDIA NIM API Configuration Guide

**Date:** May 1, 2026  
**Status:** Updated & Fixed

## Overview

The LuxeEstate chatbot uses **NVIDIA NIM (NVIDIA Inference Microservice)** for advanced AI-powered responses. If the API key is not configured, the chatbot automatically falls back to rule-based responses, ensuring 24/7 functionality.

## Quick Setup

### 1. Get Your NVIDIA API Key

1. Visit [NVIDIA Cloud APIs](https://build.nvidia.com)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Generate a new API key (for NVIDIA Cloud or NIM inference)
5. Copy the key

### 2. Configure .env File

Create or update your `.env` file in the project root with:

```env
# NVIDIA NIM API Configuration
NVIDIA_API_KEY=your-actual-api-key-here
NIM_CHAT_MODEL=meta/llama-3.1-8b-instruct
NVIDIA_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
```

### 3. Verify Configuration

The Django settings will automatically pick up these variables:

```python
# LuxeEstate/settings.py (already configured)
NVIDIA_API_KEY = config('NVIDIA_API_KEY', default='')
NIM_CHAT_MODEL = config('NIM_CHAT_MODEL', default='meta/llama-3.1-8b-instruct')
NVIDIA_NIM_ENDPOINT = config('NVIDIA_NIM_ENDPOINT', default='https://integrate.api.nvidia.com/v1')
```

## Troubleshooting

### Issue: Chatbot is not giving correct answers

**Cause:** NVIDIA NIM API is not configured or unreachable

**Solution:**
1. Check if `NVIDIA_API_KEY` is set in `.env`:
   ```bash
   echo $NVIDIA_API_KEY  # Should show your API key, not empty
   ```

2. Restart Django server for changes to take effect:
   ```bash
   python manage.py runserver
   ```

3. Check Django logs for NIM-related errors:
   - Look for messages starting with "NVIDIA NIM"
   - Error format: `NVIDIA NIM API error (status XXX)`

### Issue: API Key Authentication Failed (401)

**Cause:** Invalid or expired NVIDIA API key

**Solution:**
1. Verify your API key from [NVIDIA Cloud APIs](https://build.nvidia.com)
2. Ensure key is not truncated in `.env` file
3. Check if key has spaces or special characters
4. Generate a new API key if the current one is expired

### Issue: Model Not Found (404)

**Cause:** Incorrect model name configuration

**Solution:**
- Verify `NIM_CHAT_MODEL` is set correctly to `meta/llama-3.1-8b-instruct`
- This model is available on NVIDIA Cloud APIs

### Issue: Connection Timeout

**Cause:** 
- Endpoint is unreachable
- Network firewall blocking the API call
- NVIDIA API service is down

**Solution:**
1. Test connectivity to the endpoint:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" https://integrate.api.nvidia.com/v1/chat/completions
   ```

2. Check your internet connection
3. Verify firewall settings allow HTTPS to `integrate.api.nvidia.com`
4. Wait a few minutes and retry (NVIDIA service might be temporarily down)

## How It Works

### Response Pipeline

1. **User sends message** → Chatbot receives it
2. **Security check** → Blocks sensitive data (OTP, passwords, etc.)
3. **Out-of-scope check** → Detects weather, politics, entertainment queries
4. **Intent detection** → Identifies if user wants to buy, rent, invest, schedule visit, etc.
5. **FAQ lookup** → Checks 50+ pre-written answers
6. **NVIDIA NIM** → (Optional) Generates intelligent response if API is configured
7. **Fallback** → Uses rule-based response if NIM is unavailable
8. **Lead tracking** → Stores user information for follow-up
9. **Response sent** → Returns final message to user

### When NIM is Unavailable

If `NVIDIA_API_KEY` is not set or the API fails:
- Chatbot still works perfectly ✅
- Uses deterministic, rule-based responses
- All property searches and appointment scheduling work normally
- Only advanced AI enhancement is skipped

## Example Responses

### With NVIDIA NIM Enabled (AI-Enhanced)

```
User: "I'm looking for a 2BHK apartment in Bangalore with good amenities"

AI Response:
"I found 5 excellent 2BHK apartments in Bangalore matching your requirements. 
The top matches feature modern amenities like swimming pools, gyms, and 24/7 security. 
Prices range from ₹45L to ₹75L. Would you like me to show you more details 
or schedule a site visit for any of these properties?"
```

### Without NVIDIA NIM (Rule-Based Fallback)

```
User: "I'm looking for a 2BHK apartment in Bangalore with good amenities"

Response:
"Great! I found properties matching your criteria:
- 2BHK Luxury Flat, Indiranagar - ₹50,000,000 - Swimming Pool, Gym, 24/7 Security
- 2BHK Modern Apartment, Marathahalli - ₹45,000,000 - Gym, Parking, Lift

Would you like to schedule a visit or see more options?"
```

Both responses are helpful and functional!

## Development Notes

### Enable Debug Logging

Add to Django settings to see detailed NIM logs:

```python
LOGGING = {
    'loggers': {
        'properties.chatbot_service': {
            'level': 'DEBUG',
        }
    }
}
```

Then restart the server and check logs for NIM debug messages.

### Testing the Chatbot Locally

```python
from properties.chatbot_service import chatbot

# Test with NIM (if configured)
result = chatbot.process_message("2BHK in Pune")
print(result['message'])
print(f"Model used: {result.get('model', 'fallback')}")

# Test out-of-scope handling
result = chatbot.process_message("What's the weather?")
print(result['message'])  # Should redirect to real estate

# Test appointment scheduling
result = chatbot.process_message("Schedule visit on May 5 at 2pm")
print(result['appointment'])
```

## Configuration Summary

| Setting | Environment Variable | Default | Required |
|---------|---------------------|---------|----------|
| API Key | `NVIDIA_API_KEY` | Empty (fallback enabled) | No* |
| Chat Model | `NIM_CHAT_MODEL` | `meta/llama-3.1-8b-instruct` | No |
| Endpoint | `NVIDIA_NIM_ENDPOINT` | `https://integrate.api.nvidia.com/v1` | No |

*Required only if you want AI-enhanced responses. The chatbot works without it.

## Support

- NVIDIA NIM Docs: https://docs.nvidia.com/nim/
- Get API Key: https://build.nvidia.com
- LuxeEstate Issues: Check Django logs and error messages above
