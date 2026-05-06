import json
import logging
import requests

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .telegram_bot_fixed import handle_update, handle_callback_query

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request):
    """
    Telegram webhook endpoint for receiving updates
    
    Supports:
    - Text messages
    - Callback queries (button clicks)
    """
    if request.method == "POST":
        try:
            raw_body = request.body.decode('utf-8')
            logger.info(f"RAW WEBHOOK BODY: {raw_body[:200]}...")
            data = json.loads(raw_body)
            update_id = data.get('update_id')
            logger.info(f"[TELEGRAM] Webhook RECEIVED Update: {update_id}, chat_id: {data.get('message', {}).get('chat', {}).get('id') if 'message' in data else 'N/A'}")
            
            # Handle text messages
            if "message" in data:
                handle_update(data)
            
            # Handle button clicks (callback queries)
            elif "callback_query" in data:
                handle_callback_query(data["callback_query"])
            
            return JsonResponse({"status": "ok", "processed": True})
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e} | Body: {request.body[:100]}")
            return JsonResponse({"status": "error", "message": "Invalid JSON", "body_preview": request.body.decode('utf-8')[:100]}, status=400)
        
        except Exception as e:
            logger.error(f"Webhook Error: {e}", exc_info=True)
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"message": "Telegram webhook endpoint active", "method": request.method})


@login_required
@require_http_methods(["GET"])
def telegram_setup(request):
    """
    Setup and manage Telegram webhook
    
    GET Parameters:
    - action: 'register' or 'unregister'
    - url: webhook URL (only for register action)
    
    Example:
    /api/telegram/setup/?action=register&url=https://yourdomain.com/api/telegram/webhook/
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return JsonResponse({
            "status": "error",
            "message": "TELEGRAM_BOT_TOKEN not configured in .env"
        }, status=400)
    
    action = request.GET.get('action', '')
    
    if action == 'register':
        webhook_url = request.GET.get('url', '')
        if not webhook_url:
            return JsonResponse({
                "status": "error",
                "message": "Missing 'url' parameter. Usage: ?action=register&url=https://yourdomain.com/api/telegram/webhook/"
            }, status=400)
        
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            
            # Register webhook with Telegram
            response = requests.post(api_url, json={"url": webhook_url}, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"Telegram webhook registered: {webhook_url}")
                return JsonResponse({
                    "status": "success",
                    "message": f"Webhook registered successfully at {webhook_url}",
                    "details": result.get('result', {})
                })
            else:
                logger.error(f"Failed to register webhook: {result}")
                return JsonResponse({
                    "status": "error",
                    "message": f"Telegram API error: {result.get('description', 'Unknown error')}",
                    "details": result
                }, status=400)
        
        except Exception as e:
            logger.error(f"Error registering webhook: {e}")
            return JsonResponse({
                "status": "error",
                "message": f"Error: {str(e)}"
            }, status=500)
    
    elif action == 'unregister':
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
            
            response = requests.post(api_url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logger.info("Telegram webhook deleted")
                return JsonResponse({
                    "status": "success",
                    "message": "Webhook deleted successfully"
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "message": f"Telegram API error: {result.get('description', 'Unknown error')}",
                }, status=400)
        
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return JsonResponse({
                "status": "error",
                "message": f"Error: {str(e)}"
            }, status=500)
    
    elif action == 'info':
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
            
            response = requests.get(api_url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return JsonResponse({
                    "status": "success",
                    "webhook_info": result.get('result', {})
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "message": f"Telegram API error: {result.get('description', 'Unknown error')}",
                }, status=400)
        
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return JsonResponse({
                "status": "error",
                "message": f"Error: {str(e)}"
            }, status=500)
    
    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid action. Use 'register', 'unregister', or 'info'",
            "usage": "/api/telegram/setup/?action=register&url=https://yourdomain.com/api/telegram/webhook/"
        }, status=400)
