"""
Evanta OS — Secure Interactive Password Reset CLI
Allows an administrator or system owner to securely set or update a password
for any authorized official account without echoing input or exposing hashes.

Usage (Interactive):
    python -m app.cli.set_password

Usage (Scripted / Recovery):
    python -m app.cli.set_password --identifier baiganiprabhuteja7@gmail.com
"""

import argparse
import getpass
import sys
from sqlalchemy import func, or_, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def set_user_password(identifier: str = None, new_password: str = None) -> bool:
    db = SessionLocal()
    try:
        if not identifier:
            print("==================================================")
            print("   Evanta OS — Secure Password Management CLI    ")
            print("   Single Station Scope: Hyderabad, Telangana     ")
            print("==================================================")
            identifier = input("Enter official's email or username: ").strip()

        if not identifier:
            print("[!] Error: Email or username cannot be empty.")
            return False

        norm_id = identifier.strip().lower()

        # Find the target user
        user = db.scalar(
            select(User).where(
                or_(
                    func.lower(User.email) == norm_id,
                    func.lower(User.username) == norm_id,
                )
            )
        )

        if not user:
            print(f"[!] Error: No user account found matching '{identifier}'.")
            print("    If this is a new administrator, run: python -m app.cli.bootstrap_admin --force")
            return False

        if not new_password:
            while True:
                p1 = getpass.getpass("Enter new secure password (min 8 chars): ")
                if len(p1) < 8:
                    print("[!] Password must be at least 8 characters long. Try again.")
                    continue
                p2 = getpass.getpass("Confirm new secure password: ")
                if p1 != p2:
                    print("[!] Passwords do not match. Try again.")
                    continue
                new_password = p1
                break
        else:
            if len(new_password) < 8:
                print("[!] Error: Password must be at least 8 characters long.")
                return False

        # Hash with Argon2id and reset failure counters
        user.password_hash = hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.is_active = True
        db.commit()

        print(f"\n[+] Password successfully updated for '{user.email}' (role: {user.role}).")
        print("    Account lockout and failed attempt counters have been reset to 0.")
        print("    Account status: Active\n")
        return True

    except Exception as e:
        db.rollback()
        print(f"\n[!] Error updating password: {e}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Evanta OS Secure Password Reset CLI"
    )
    parser.add_argument(
        "--identifier",
        type=str,
        help="Email address or username of account to update",
    )
    parser.add_argument(
        "--password",
        type=str,
        help="New password (optional; if omitted, prompts securely without echoing)",
    )

    args = parser.parse_args()
    success = set_user_password(identifier=args.identifier, new_password=args.password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
