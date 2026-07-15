from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import GitFServices

@csrf_exempt
def GitHubWebHookReciever(request):
    if request.method != 'POST':
        return JsonResponse(
            {"error": "Method Not Allowed", "details": "Only HTTP POST requests are supported."},
            status=405
        )
    raw_payload = request.body
    success = GitFServices.process_webhook(raw_payload)

    if success:
        return JsonResponse(
            {"status": "SUCCESS", "message": "Repository and commit data parsed and logged successfully."},
            status=201
        )
    
    else:
        return JsonResponse(
            {"status": "ERROR", "message": "Failed to parse payload. Check structure and required fields."},
            status=400
        )