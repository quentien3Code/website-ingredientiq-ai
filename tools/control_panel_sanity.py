"""End-to-end sanity check for the React /control-panel + Django /master APIs.

Runs against a local SQLite DB file so it won't affect production.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _set_env() -> Path:
    root = _project_root()

    # When executed as a script (python tools/...), sys.path[0] is the tools/
    # directory. Add repo root so imports like `foodanalysis` work.
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    # Sanity: ensure the Django project package is importable.
    try:
        __import__("foodanalysis")
    except Exception as exc:
        print("DEBUG unable to import foodanalysis")
        print(f"DEBUG root={root_str}")
        print(f"DEBUG sys.path[:3]={sys.path[:3]}")
        raise exc

    db_path = root / "tmp_control_panel_sanity.sqlite3"
    try:
        db_path.unlink(missing_ok=True)
    except Exception:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodanalysis.settings")
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("ALLOW_INSECURE_DEV_SECRET_KEY", "1")
    os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    return db_path


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    db_path = _set_env()

    import django  # noqa: E402

    django.setup()

    from django.core.management import call_command  # noqa: E402
    from django.test import Client  # noqa: E402

    admin_email = "admin@ingredientiq.ai"
    admin_password = "AdminPass123!"

    # 1) DB migrations
    call_command("migrate", interactive=False, verbosity=0)

    # 2) Ensure a SuperAdmin exists for control-panel login
    call_command(
        "reset_superadmin",
        "--email",
        admin_email,
        "--full-name",
        "Admin",
        "--password",
        admin_password,
        verbosity=0,
    )

    c = Client()

    # 3) Control panel HTML shell loads
    r = c.get("/control-panel/")
    _assert(r.status_code == 200, f"/control-panel/ status {r.status_code}")
    _assert(
        (r.get("Content-Type") or "").startswith("text/html"),
        f"/control-panel/ content-type {r.get('Content-Type')}",
    )
    body = r.content.decode("utf-8", errors="ignore")
    _assert("/control-panel/static/" in body, "control-panel HTML missing static asset paths")

    # 4) Key admin JS asset loads and has server-time base URL rewrites
    js_path = "/control-panel/static/js/main.25640e89.js"
    r = c.get(js_path)
    _assert(r.status_code == 200, f"{js_path} status {r.status_code}")
    js_bytes = b"".join(r.streaming_content) if getattr(r, "streaming", False) else r.content
    js_text = js_bytes.decode("utf-8", errors="ignore")
    _assert(
        "https://ingredientiq.ai/master" not in js_text,
        "admin bundle still contains absolute https://ingredientiq.ai/master",
    )
    _assert(
        "https://ingredientiq.ai/web" not in js_text,
        "admin bundle still contains absolute https://ingredientiq.ai/web",
    )
    _assert("/master" in js_text, "admin bundle missing /master relative API base")

    # 5) Login API returns JWT access token
    login_path = "/master/login/"
    r = c.post(login_path, {"email": admin_email, "password": admin_password})
    _assert(r.status_code == 200, f"{login_path} status {r.status_code}")
    payload = json.loads(r.content.decode("utf-8", errors="ignore") or "{}")
    _assert(payload.get("success") is True, f"login did not succeed: {payload}")
    token = ((payload.get("data") or {}) or {}).get("token")
    _assert(isinstance(token, str) and token, "login did not return an access token")

    # 6) Authenticated API calls work with Bearer token
    users_path = "/master/users/"
    r = c.get(users_path, HTTP_AUTHORIZATION=f"Bearer {token}")
    _assert(r.status_code == 200, f"{users_path} status {r.status_code}")

    profile_path = "/master/profileview"
    r = c.get(profile_path, HTTP_AUTHORIZATION=f"Bearer {token}")
    _assert(r.status_code in (200, 201), f"{profile_path} status {r.status_code}")

    print("OK control-panel sanity")
    print(f"db={db_path.name}")
    print("control_panel_html=200")
    print("admin_js_rewrite=ok")
    print("login=ok")
    print("auth_users=ok")
    print("auth_profile=ok")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAIL control-panel sanity")
        print(str(exc))
        return_code = 1
        try:
            sys.exit(return_code)
        except SystemExit:
            raise
