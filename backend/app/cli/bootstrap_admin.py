"""
Evanta OS — One-Time First Administrator Bootstrap CLI
Usage (Interactive):
    python -m app.cli.bootstrap_admin

Usage (Non-interactive / Scripted):
    python -m app.cli.bootstrap_admin --email admin@evanta.local --password "StrongPass123!" --name "Station Administrator"
"""

import argparse
import getpass
import sys
from sqlalchemy import func, or_, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def bootstrap_admin(
    email: str = None,
    username: str = None,
    name: str = None,
    password: str = None,
    force: bool = False,
) -> bool:
    db = SessionLocal()
    try:
        # Check if an active administrator already exists
        existing_admin = db.scalar(
            select(User).where(User.role == "admin", User.is_active == True)
        )
        if existing_admin and not force:
            print("\n[!] ERROR: An active administrator account already exists in Evanta OS.")
            print(f"    Existing Admin Email: {existing_admin.email}")
            print("    One-time bootstrap is REFUSED to protect station security.")
            print("    To perform an authorized recovery, re-run with --force flag.\n")
            return False

        # Interactive prompts if arguments were not provided
        if not email:
            print("==================================================")
            print("   Evanta OS — Secure First Administrator Setup   ")
            print("   Single Station Scope: Hyderabad, Telangana     ")
            print("==================================================")
            email = input("Enter administrator email address: ").strip()

        if not email:
            print("[!] Error: Email address cannot be empty.")
            return False

        if not username:
            default_user = email.split("@")[0]
            entered_username = input(f"Enter administrator username [{default_user}]: ").strip()
            username = entered_username if entered_username else default_user

        if not name:
            entered_name = input("Enter administrator full name [Evanta Administrator]: ").strip()
            name = entered_name if entered_name else "Evanta Administrator"

        if not password:
            while True:
                p1 = getpass.getpass("Enter secure password (min 8 chars): ")
                if len(p1) < 8:
                    print("[!] Password must be at least 8 characters long. Try again.")
                    continue
                p2 = getpass.getpass("Confirm secure password: ")
                if p1 != p2:
                    print("[!] Passwords do not match. Try again.")
                    continue
                password = p1
                break
        else:
            if len(password) < 8:
                print("[!] Error: Password must be at least 8 characters long.")
                return False

        norm_email = email.strip().lower()
        norm_username = username.strip().lower() if username else None

        # Check if user already exists
        target_user = db.scalar(
            select(User).where(
                or_(
                    func.lower(User.email) == norm_email,
                    func.lower(User.username) == norm_username if norm_username else False,
                )
            )
        )

        hashed = hash_password(password)

        if target_user:
            # Upgrade or reset existing user
            target_user.full_name = name
            target_user.email = norm_email
            target_user.username = norm_username
            target_user.password_hash = hashed
            target_user.role = "admin"
            target_user.is_active = True
            target_user.failed_login_attempts = 0
            target_user.locked_until = None
            db.commit()
            print(f"\n[+] Administrator '{norm_email}' successfully updated/recovered.")
        else:
            new_admin = User(
                full_name=name,
                email=norm_email,
                username=norm_username,
                password_hash=hashed,
                role="admin",
                is_active=True,
                failed_login_attempts=0,
                locked_until=None,
            )
            db.add(new_admin)
            db.commit()
            print(f"\n[+] First Administrator '{norm_email}' successfully created in Evanta OS.")

        print("    Role: Administrator (Full Station & User Management Privileges)")
        print("    Status: Active\n")
        return True
    except Exception as e:
        db.rollback()
        print(f"\n[!] Failed to bootstrap administrator: {e}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Evanta OS First Administrator Secure Setup"
    )
    parser.add_argument("--email", type=str, help="Administrator email address")
    parser.add_argument("--username", type=str, help="Administrator username")
    parser.add_argument("--name", type=str, help="Administrator full name")
    parser.add_argument("--password", type=str, help="Administrator password")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow resetting/recovering an administrator account if one already exists",
    )

    args = parser.parse_args()

    success = bootstrap_admin(
        email=args.email,
        username=args.username,
        name=args.name,
        password=args.password,
        force=args.force,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
