#!/usr/bin/env python3
"""
Create Superuser Script for AI Meeting Assistant

This script allows you to create additional superusers for the system.
"""

import asyncio
import sys
from getpass import getpass

from sqlmodel import Session
from app import crud
from app.core.db import engine
from app.models import UserCreate


def create_superuser():
    """Create a new superuser interactively"""
    
    print("🚀 AI Meeting Assistant - Create Superuser")
    print("=" * 50)
    
    # Get user input
    email = input("Enter superuser email: ").strip()
    if not email:
        print("❌ Email is required!")
        return False
    
    # Get password securely
    password = getpass("Enter password: ").strip()
    if not password:
        print("❌ Password is required!")
        return False
    
    # Confirm password
    password_confirm = getpass("Confirm password: ").strip()
    if password != password_confirm:
        print("❌ Passwords don't match!")
        return False
    
    # Get full name (optional)
    full_name = input("Enter full name (optional): ").strip() or None
    
    try:
        with Session(engine) as session:
            # Check if user already exists
            existing_user = crud.get_user_by_email(session=session, email=email)
            if existing_user:
                print(f"❌ User with email '{email}' already exists!")
                
                # Ask if they want to make existing user a superuser
                make_super = input("Make this user a superuser? (y/N): ").strip().lower()
                if make_super in ['y', 'yes']:
                    existing_user.is_superuser = True
                    session.add(existing_user)
                    session.commit()
                    print(f"✅ User '{email}' is now a superuser!")
                    return True
                else:
                    return False
            
            # Create new superuser
            user_create = UserCreate(
                email=email,
                password=password,
                full_name=full_name,
                is_superuser=True,
                is_active=True
            )
            
            user = crud.create_user(session=session, user_create=user_create)
            
            print(f"✅ Superuser created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.full_name or 'Not provided'}")
            print(f"   ID: {user.id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating superuser: {str(e)}")
        return False


def list_superusers():
    """List all existing superusers"""
    
    print("📋 Current Superusers")
    print("=" * 30)
    
    try:
        with Session(engine) as session:
            from sqlmodel import select
            from app.models import User
            
            superusers = session.exec(
                select(User).where(User.is_superuser == True)
            ).all()
            
            if not superusers:
                print("No superusers found.")
                return
            
            for i, user in enumerate(superusers, 1):
                print(f"{i}. {user.email}")
                print(f"   Name: {user.full_name or 'Not provided'}")
                print(f"   Active: {'✅' if user.is_active else '❌'}")
                print(f"   ID: {user.id}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing superusers: {str(e)}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_superusers()
            return
        elif command == "help":
            print("Usage:")
            print("  python scripts/create_superuser.py        - Create a new superuser")
            print("  python scripts/create_superuser.py list   - List all superusers")
            print("  python scripts/create_superuser.py help   - Show this help")
            return
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for usage information.")
            return
    
    # Default action: create superuser
    success = create_superuser()
    
    if success:
        print("\n🎉 You can now use this superuser to:")
        print("   • Access admin endpoints")
        print("   • Manage other users")
        print("   • Create meetings for testing")
        print("   • Access the API documentation at /docs")
    else:
        print("\n❌ Superuser creation failed. Please try again.")


if __name__ == "__main__":
    main() 