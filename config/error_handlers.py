"""
Aureon SaaS Platform - Custom Error Handlers
Rhematek Production Shield

Custom error pages for production use.
"""

import uuid
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import requires_csrf_token

logger = logging.getLogger(__name__)


def is_api_request(request):
    """Check if this is an API request expecting JSON response."""
    accept = request.META.get('HTTP_ACCEPT', '')
    content_type = request.META.get('CONTENT_TYPE', '')

    return (
        'application/json' in accept or
        'application/json' in content_type or
        request.path.startswith('/api/')
    )


@requires_csrf_token
def handler404(request, exception=None):
    """Custom 404 error handler."""
    if is_api_request(request):
        return JsonResponse({
            "error": "Not Found",
            "message": "The requested resource was not found.",
            "status_code": 404,
        }, status=404)

    return render(request, 'errors/404.html', status=404)


@requires_csrf_token
def handler500(request):
    """Custom 500 error handler."""
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())[:8]
    logger.error(f"Internal Server Error - Request ID: {request_id}")

    if is_api_request(request):
        return JsonResponse({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
            "status_code": 500,
        }, status=500)

    return render(request, 'errors/500.html', {
        'request_id': request_id,
    }, status=500)


@requires_csrf_token
def handler403(request, exception=None):
    """Custom 403 error handler."""
    if is_api_request(request):
        return JsonResponse({
            "error": "Forbidden",
            "message": "You don't have permission to access this resource.",
            "status_code": 403,
        }, status=403)

    return render(request, 'errors/403.html', status=403)


@requires_csrf_token
def handler400(request, exception=None):
    """Custom 400 error handler."""
    if is_api_request(request):
        return JsonResponse({
            "error": "Bad Request",
            "message": "The request could not be processed.",
            "status_code": 400,
        }, status=400)

    # Reuse 404 template for bad requests
    return render(request, 'errors/404.html', status=400)


def handler429(request, exception=None):
    """Custom 429 rate limit error handler."""
    if is_api_request(request):
        return JsonResponse({
            "error": "Too Many Requests",
            "message": "You have exceeded the rate limit. Please wait before retrying.",
            "retry_after": 60,
            "status_code": 429,
        }, status=429)

    return render(request, 'errors/429.html', status=429)
