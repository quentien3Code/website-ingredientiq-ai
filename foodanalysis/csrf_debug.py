import json
import logging
import os
import socket

from django.conf import settings
from django.views.csrf import csrf_failure as default_csrf_failure


_logger = logging.getLogger('foodanalysis.admin_debug')


def _enabled() -> bool:
    return os.getenv('ADMIN_DEBUG', '').strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def _truncate(value: str, max_len: int = 200) -> str:
    if not value:
        return ''
    value = str(value)
    return value if len(value) <= max_len else value[:max_len] + '…'


def csrf_failure(request, reason='', template_name='403_csrf.html'):
    """CSRF failure view that can emit safe, structured diagnostics.

    Enabled via ADMIN_DEBUG=1.
    Never logs cookie/token values.
    """

    if _enabled():
        payload = {
            'event': 'csrf_failure',
            'method': getattr(request, 'method', None),
            'path': getattr(request, 'path', None),
            'is_secure': bool(getattr(request, 'is_secure', lambda: False)()),
            'host': _truncate(getattr(request, 'get_host', lambda: '')()),
            'origin': _truncate(request.META.get('HTTP_ORIGIN', '')),
            'referer': _truncate(request.META.get('HTTP_REFERER', '')),
            'has_session_cookie': settings.SESSION_COOKIE_NAME in request.COOKIES,
            'has_csrf_cookie': settings.CSRF_COOKIE_NAME in request.COOKIES,
            'reason': _truncate(reason, 300),
            'pid': os.getpid(),
            'hostname': socket.gethostname(),
        }
        try:
            _logger.warning(json.dumps(payload, separators=(',', ':'), sort_keys=True))
        except Exception:
            pass

    return default_csrf_failure(request, reason=reason, template_name=template_name)
