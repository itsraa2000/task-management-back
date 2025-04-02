from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.urls import resolve
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.exceptions import ValidationError

def custom_exception_handler(exc, context):
    # Handle authentication errors
    if isinstance(exc, (InvalidToken, TokenError)):
        return JsonResponse({
            'error': 'Authentication Error',
            'message': 'Invalid or expired token. Please login again.',
            'status': 'error'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Handle login errors
    if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
        if 'detail' in exc.detail and 'No active account found with the given credentials' in str(exc.detail['detail']):
            return JsonResponse({
                'error': 'Login Error',
                'message': 'Invalid username or password.',
                'status': 'error'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Handle validation errors
    if isinstance(exc, ValidationError):
        return JsonResponse({
            'error': 'Validation Error',
            'message': str(exc),
            'status': 'error'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Call REST framework's default exception handler
    response = exception_handler(exc, context)
    if response is not None:
        return response
    
    # Handle 404 errors
    if isinstance(exc, Exception):
        try:
            resolve(context['request'].path)
        except:
            return JsonResponse({
                'error': 'Not Found',
                'message': 'The requested endpoint was not found on this server.',
                'correct_endpoint': '/api/auth/login/',
                'status': 'error'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Handle other errors
    return JsonResponse({
        'error': 'Internal Server Error',
        'message': str(exc),
        'status': 'error'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 