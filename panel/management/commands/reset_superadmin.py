from __future__ import annotations

import os
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from foodinfo.models import User
from panel.models import SuperAdmin


class Command(BaseCommand):
    help = "Create or reset the SuperAdmin used by the /control-panel/ admin UI."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="admin@ingredientiq.ai",
            help="Email for the SuperAdmin account (default: admin@ingredientiq.ai)",
        )
        parser.add_argument(
            "--full-name",
            default="Admin",
            help="Full name to set on the account (default: Admin)",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="(Not recommended) Set password from CLI argument.",
        )
        parser.add_argument(
            "--password-env",
            default=None,
            help="Read password from an environment variable name (recommended for CI).",
        )

    def handle(self, *args, **options):
        email: str = (options.get("email") or "").strip().lower()
        full_name: str = (options.get("full_name") or "").strip() or "Admin"

        if not email:
            raise CommandError("--email is required")

        password = self._get_password(options)

        admin = SuperAdmin.objects.filter(email=email).first()
        created = False

        if admin is None:
            # If a regular User already exists with this email, "upgrade" it to SuperAdmin
            # (multi-table inheritance requires creating the child table row).
            base_user = User.objects.filter(email=email).first()
            if base_user is not None:
                admin = SuperAdmin.objects.create(user_ptr=base_user, is_super_admin=True)
                created = True
            else:
                admin = SuperAdmin.objects.create_user(email=email, full_name=full_name, password=password)
                created = True

        if full_name and admin.full_name != full_name:
            admin.full_name = full_name
        admin.set_password(password)

        # Ensure admin privileges for both Django admin and control-panel auth
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_super_admin = True
        admin.is_active = True
        admin.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created SuperAdmin: {email}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Reset SuperAdmin password: {email}"))

    def _get_password(self, options) -> str:
        password = options.get("password")
        if password:
            return str(password)

        password_env = options.get("password_env")
        if password_env:
            env_value = os.getenv(str(password_env))
            if not env_value:
                raise CommandError(f"Environment variable '{password_env}' is not set")
            return env_value

        # Interactive prompt
        p1 = getpass("New password: ")
        p2 = getpass("Confirm password: ")
        if p1 != p2:
            raise CommandError("Passwords do not match")
        if len(p1) < 8:
            raise CommandError("Password must be at least 8 characters")
        return p1
