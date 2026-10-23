"""Database migration script to safely upgrade from old schema to new UUID-based schema."""

import sys
import os
import uuid
from datetime import datetime, date
from decimal import Decimal

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    test_connection, SessionLocal, Base, engine,
    User, LegacyUser
)
from sqlalchemy import text
import json

def backup_existing_data():
    """Backup existing data before migration."""
    print("📦 Backing up existing data...")
    
    db = SessionLocal()
    try:
        # Check if legacy users table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """))
        
        table_exists = result.scalar()
        
        if table_exists:
            # Backup existing users data
            result = db.execute(text("SELECT * FROM users"))
            users_data = []
            for row in result:
                if hasattr(row, '_asdict'):
                    users_data.append(dict(row._asdict()))
                else:
                    # Handle different SQLAlchemy versions
                    users_data.append({
                        'id': row[0],
                        'name': row[1] if len(row) > 1 else None,
                        'email': row[2] if len(row) > 2 else None,
                        'address': row[3] if len(row) > 3 else None,
                        'phone': row[4] if len(row) > 4 else None
                    })
            
            # Save backup to file
            backup_file = 'data_backup.json'
            with open(backup_file, 'w') as f:
                json.dump(users_data, f, indent=2, default=str)
            
            print(f"✅ Backed up {len(users_data)} users to {backup_file}")
            return users_data
        else:
            print("ℹ️  No existing users table found")
            return []
            
    except Exception as e:
        print(f"⚠️  Warning: Could not backup existing data: {e}")
        return []
    finally:
        db.close()

def drop_all_tables():
    """Drop all existing tables."""
    print("🧹 Dropping all existing tables...")
    
    db = SessionLocal()
    try:
        # Drop tables in correct order to handle dependencies
        tables_to_drop = [
            'agent_interactions',
            'inventory_transactions', 
            'supplies',
            'supply_categories',
            'equipment',
            'equipment_categories',
            'staff',
            'beds',
            'rooms',
            'departments',
            'patients',
            'users',
            'legacy_users'
        ]
        
        for table in tables_to_drop:
            try:
                db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  ✓ Dropped {table}")
            except Exception as e:
                print(f"  ⚠️  Could not drop {table}: {e}")
        
        db.commit()
        print("✅ All tables dropped successfully")
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_new_schema():
    """Create the new schema with UUID support."""
    print("🏗️  Creating new database schema...")
    
    try:
        # Enable UUID extension
        db = SessionLocal()
        db.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        db.commit()
        db.close()
        print("✅ UUID extension enabled")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ New schema created successfully")
        
    except Exception as e:
        print(f"❌ Error creating new schema: {e}")
        raise

def migrate_legacy_data(backup_data):
    """Migrate backed up data to new schema."""
    if not backup_data:
        print("ℹ️  No legacy data to migrate")
        return
    
    print("🔄 Migrating legacy data to new schema...")
    
    db = SessionLocal()
    try:
        # Migrate users to legacy_users table for backward compatibility
        for user_data in backup_data:
            if user_data.get('name') and user_data.get('email'):
                legacy_user = LegacyUser(
                    name=user_data['name'],
                    email=user_data['email'],
                    address=user_data.get('address', ''),
                    phone=user_data.get('phone', '')
                )
                db.add(legacy_user)
        
        db.commit()
        print(f"✅ Migrated {len(backup_data)} users to legacy_users table")
        
    except Exception as e:
        print(f"❌ Error migrating data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_migration():
    """Verify that the migration was successful."""
    print("🔍 Verifying migration...")
    
    db = SessionLocal()
    try:
        # Check that all tables exist
        required_tables = [
            'users', 'departments', 'patients', 'rooms', 'beds', 'staff',
            'equipment_categories', 'equipment', 'supply_categories', 'supplies',
            'inventory_transactions', 'agent_interactions', 'legacy_users'
        ]
        
        for table in required_tables:
            result = db.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
            """))
            
            if not result.scalar():
                raise Exception(f"Table {table} was not created")
        
        print("✅ All required tables exist")
        
        # Check legacy data
        legacy_count = db.query(LegacyUser).count()
        print(f"✅ Legacy users preserved: {legacy_count}")
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        raise
    finally:
        db.close()

def main():
    """Main migration function."""
    print("🏥 Hospital Management System Database Migration")
    print("=" * 55)
    
    # Test connection
    print("1. Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your PostgreSQL setup.")
        return False
    
    try:
        # Backup existing data
        backup_data = backup_existing_data()
        
        # Drop all tables
        drop_all_tables()
        
        # Create new schema
        create_new_schema()
        
        # Migrate legacy data
        migrate_legacy_data(backup_data)
        
        # Verify migration
        verify_migration()
        
        print("\n🎉 Database migration completed successfully!")
        print("\nNext steps:")
        print("- Run 'python setup_database.py' to create sample data")
        print("- Run 'python comprehensive_server.py' to start the MCP server")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\n💡 You may need to:")
        print("- Restore from backup if needed")
        print("- Check PostgreSQL logs for more details")
        print("- Ensure you have proper database permissions")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
