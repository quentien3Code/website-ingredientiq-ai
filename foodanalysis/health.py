from django.http import JsonResponse

def health(request):
    """Simple health check endpoint for Railway deployment.
    
    This endpoint must:
    - Have no external dependencies
    - Always return 200 OK
    - Be as simple as possible to avoid any import errors
    """
    return JsonResponse({"status": "ok"})
