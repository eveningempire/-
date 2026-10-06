#!/usr/bin/env python
"""Create an administrator for the PHM platform."""

import getpass
import os
import re
import sys

import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phm_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

User = get_user_model()
HAS_ROLE_FIELD = any(field.name == "role" for field in User._meta.get_fields())


def validate_username(username):
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must contain at least 3 characters."
    if len(username) > 150:
        return False, "Username cannot exceed 150 characters."
    if not re.fullmatch(r"[\w.-]+", username):
        return False, "Username may contain letters, digits, _, -, and . only."
    if User.objects.filter(username=username).exists():
        return False, f"Username '{username}' already exists."
    return True, ""


def validate_email_address(email):
    if not email:
        return True, ""
    try:
        validate_email(email)
    except ValidationError:
        return False, "Invalid email address."
    return True, ""


def validate_password(password):
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."
    return True, ""


def interactive_create_admin():
    print("Enter administrator account information.")
    while True:
        username = input("Username: ").strip()
        valid, message = validate_username(username)
        if valid:
            break
        print(f"Error: {message}")
    while True:
        email = input("Email (optional): ").strip()
        valid, message = validate_email_address(email)
        if valid:
            break
        print(f"Error: {message}")
    while True:
        password = getpass.getpass("Password: ")
        valid, message = validate_password(password)
        if not valid:
            print(f"Error: {message}")
            continue
        if password == getpass.getpass("Confirm password: "):
            break
        print("Error: passwords do not match.")
    first_name = input("Display name (optional): ").strip()
    return {
        "username": username,
        "email": email or f"{username}@cmg-platform.local",
        "password": password,
        "first_name": first_name or "System Administrator",
    }


def quick_create_admin():
    username, password = "admin", "admin123456"
    if User.objects.filter(username=username).exists():
        print("Error: username 'admin' already exists.")
        return None
    print(f"Username: {username}\nPassword: {password}")
    if input("Create this account? (y/n): ").strip().lower() not in {"y", "yes"}:
        print("Creation cancelled.")
        return None
    return {"username": username, "email": "admin@cmg-platform.local", "password": password, "first_name": "System Administrator"}


def create_superuser(data):
    try:
        fields = dict(
            username=data["username"], email=data["email"], password=data["password"],
            first_name=data["first_name"], is_active=True,
            is_staff=True, is_superuser=True,
        )
        if HAS_ROLE_FIELD:
            fields["role"] = "admin"
        user = User.objects.create_user(**fields)
    except Exception as exc:
        print(f"Error creating administrator: {exc}")
        return False
    print(f"Administrator '{user.username}' created successfully.")
    print("You can sign in at http://localhost:8000")
    return True


def main():
    admin_filter = {"role": "admin"} if HAS_ROLE_FIELD else {"is_staff": True, "is_superuser": True}
    count = User.objects.filter(**admin_filter).count()
    if count and input(f"There are already {count} administrator account(s). Create another? (y/n): ").strip().lower() not in {"y", "yes"}:
        return
    data = quick_create_admin() if "--quick" in sys.argv or "-q" in sys.argv else interactive_create_admin()
    if data is not None and not create_superuser(data):
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCreation cancelled.")
