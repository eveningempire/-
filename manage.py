#!/usr/bin/env python
"""
Entry point for Django's command鈥恖ine utility for administrative tasks.

This script sets the default settings module and delegates to Django's
``execute_from_command_line``. It lives at the project root so that the
framework can discover the package structure correctly.
"""
import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phm_backend.settings")
    try:
        from django.core.management import execute_from_command_line  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it is installed and available "
            "on your PYTHONPATH environment variable. Did you forget to "
            "activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
