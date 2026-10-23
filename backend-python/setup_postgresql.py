#!/usr/bin/env python3
"""
Setup script for Hospital Management System with PostgreSQL.
This script helps set up PostgreSQL database and migrate existing data.
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_postgresql():
    """Check if PostgreSQL is installed and running."""
    print("🔍 Checking PostgreSQL installation...")
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL not found in PATH")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL not installed or not in PATH")
        return False

def create_database():
    """Create the hospital_management database."""
    print("🗄️  Creating database...")
    
    # Read database configuration from .env
    db_name = "hospital_management"
    db_user = "postgres"  # Default user
    
    try:
        # Try to create database
        subprocess.run([
            "psql", "-U", db_user, "-c", f"CREATE DATABASE {db_name};"
        ], check=True)
        print(f"✅ Database '{db_name}' created successfully!")
        return True
    except subprocess.CalledProcessError:
        print(f"⚠️  Database '{db_name}' might already exist or check your PostgreSQL configuration")
        return True  # Continue anyway

def setup_database():
    """Set up database tables and migrate data."""
    print("🏗️  Setting up database tables...")
    try:
        from database import create_tables, migrate_json_to_db, test_connection
        
        if test_connection():
            create_tables()
            migrate_json_to_db()
            print("✅ Database setup completed!")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except ImportError as e:
        print(f"❌ Cannot import database modules: {e}")
        print("Make sure all dependencies are installed")
        return False

def main():
    """Main setup function."""
    print("🏥 Hospital Management System - PostgreSQL Setup")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("Setup failed. Please check the error messages above.")
        return
    
    # Step 2: Check PostgreSQL
    if not check_postgresql():
        print("""
❌ PostgreSQL Setup Required:

Windows:
1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password for 'postgres' user
4. Add PostgreSQL bin directory to PATH

macOS:
1. brew install postgresql
2. brew services start postgresql

Linux (Ubuntu/Debian):
1. sudo apt update
2. sudo apt install postgresql postgresql-contrib
3. sudo systemctl start postgresql

After installation, update the .env file with your database credentials.
        """)
        return
    
    # Step 3: Create database
    create_database()
    
    # Step 4: Setup tables and migrate data
    if setup_database():
        print("""
🎉 Setup Complete!

Your Hospital Management System is now configured with PostgreSQL.

Next steps:
1. Update .env file with your PostgreSQL credentials:
   - DB_USER=your_username
   - DB_PASSWORD=your_password
   - DB_HOST=localhost
   - DB_PORT=5432
   - DB_NAME=hospital_management

2. Start the server:
   python server.py

3. Test the connection:
   python database.py
        """)
    else:
        print("❌ Setup failed. Please check your PostgreSQL configuration.")

if __name__ == "__main__":
    main()
