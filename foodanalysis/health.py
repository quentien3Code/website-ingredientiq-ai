import os

from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse


def healthz(_request):
    """Liveness probe.

    Contract:
    - Always returns HTTP 200 if the process can answer HTTP.
    - No external dependency checks.
    - Never returns PHI/PII.
    """

    return HttpResponse("OK", status=200, content_type="text/plain")


def _env_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def readyz(_request):
    """Readiness probe.

    Contract:
    - Returns HTTP 200 only when safe to receive real traffic.
    - Returns HTTP 503 while not ready.
    - Response body is intentionally minimal.

    Controls (env vars):
    - READYZ_REQUIRED_ENV: comma-separated env var names that must be set.
    - READYZ_CHECK_DB: 'true'/'false'/'auto'.
        - auto => check DB only when DATABASE_URL is present.
    """

    required_env = [
        name.strip()
        for name in os.getenv("READYZ_REQUIRED_ENV", "").split(",")
        if name.strip()
    ]
    for env_name in required_env:
        if not os.getenv(env_name):
            return HttpResponse("NOT_READY", status=503, content_type="text/plain")

    check_db_setting = os.getenv("READYZ_CHECK_DB", "auto").strip().lower()
    if check_db_setting not in {"true", "false", "auto"}:
        check_db_setting = "auto"

    should_check_db = (
        check_db_setting == "true"
        or (check_db_setting == "auto" and bool(os.getenv("DATABASE_URL")))
    )

    if should_check_db:
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            return HttpResponse("NOT_READY", status=503, content_type="text/plain")
        except Exception:
            return HttpResponse("NOT_READY", status=503, content_type="text/plain")

    return HttpResponse("OK", status=200, content_type="text/plain")
