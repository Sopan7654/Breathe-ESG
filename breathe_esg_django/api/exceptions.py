"""
exceptions.py — Custom DRF exception handler.
Formats all errors consistently as { "error": "..." } to match C# behavior.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Maps Python exceptions to HTTP responses exactly like the C# controller try/catch blocks:
      - ValueError / AssertionError  → 400 Bad Request
      - KeyError / DoesNotExist      → 404 Not Found
      - PermissionError              → 409 Conflict (locked record)
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, KeyError):
        return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, (ValueError, AssertionError)):
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, PermissionError):
        return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)

    # Unhandled — re-raise so Django gives a 500
    return None
