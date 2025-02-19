from rest_framework.response import Response


def fm_response(status_code, message, data=None, error_code=None, errors=None):
    """
    Utility function to structure API responses in a consistent format.

    :param status_code: HTTP status code (e.g., 200, 400, 401, etc.)
    :param message: Main message to display in the response
    :param data: Actual response data (default: None)
    :param error_code: Custom error code string (default: None)
    :param errors: Additional error details (default: None)
    :return: JSON Response object
    """
    return Response({
        "status": {
            "statusCode": status_code,
            "errorCode": error_code,
            "message": message,
            "errors": errors
        },
        "data": data
    }, status=status_code)
