"""
Custom middleware to bypass ALLOWED_HOSTS check in development
"""
from django.conf import settings
from django.middleware.common import CommonMiddleware
from django.core.exceptions import DisallowedHost


class FlexibleCommonMiddleware(CommonMiddleware):
    """
    Custom CommonMiddleware that skips ALLOWED_HOSTS validation in DEBUG mode.
    This prevents 400 Bad Request errors during local development.
    """
    def process_request(self, request):
        # Skip ALLOWED_HOSTS check in DEBUG mode
        if settings.DEBUG:
            # Temporarily allow any host by adding it to ALLOWED_HOSTS
            host = request.get_host().split(':')[0]  # Remove port
            if host not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(host)
        
        # Call parent's process_request
        return super().process_request(request)

