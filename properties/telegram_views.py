import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .telegram_bot import handle_update


@csrf_exempt
def telegram_webhook(request):

    if request.method == "POST":

        try:
            data = json.loads(request.body)

            print("Telegram Update:", data)

            handle_update(data)

            return JsonResponse({
                "status": "ok"
            })

        except Exception as e:
            print("Webhook Error:", e)

            return JsonResponse({
                "status": "error",
                "message": str(e)
            })

    return JsonResponse({
        "message": "Webhook endpoint working"
    })