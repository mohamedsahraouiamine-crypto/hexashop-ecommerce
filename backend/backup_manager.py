"""
Database Backup Manager for Hexashop
Simple, automated PostgreSQL backup system with Telegram notifications
"""
import os
import subprocess
import schedule
import time
import threading
from datetime import datetime
from flask import current_app
import psycopg2
import requests  # ADDED: For Telegram API calls
from database import db

class BackupManager:
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = "backups"
        self.max_backups = 96  # Keep last 96 backups (48 hours of 30-min backups)
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def init_app(self, app):
        self.app = app
    
    def get_database_url(self):
        """Extract database connection details from app config"""
        database_url = self.app.config['SQLALCHEMY_DATABASE_URI']
        if database_url.startswith('postgresql://'):
            return database_url
        return database_url
    
    def _send_to_telegram(self, backup_file, backup_type):
        """Send backup file to Telegram bot"""
        try:
            # Get Telegram credentials from environment variables
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            chat_id = os.environ.get('TELEGRAM_CHAT_ID')
            
            if not bot_token or not chat_id:
                print("⚠️ Telegram credentials not configured. Skipping Telegram upload.")
                return False
            
            # Prepare the message
            file_size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            caption = (
                f"🔐 Hexashop Database Backup\n"
                f"📅 {timestamp}\n"
                f"📁 Type: {backup_type}\n"
                f"📊 Size: {file_size_mb:.2f} MB\n"
                f"✅ Backup created successfully"
            )
            
            # Send file to Telegram
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            
            with open(backup_file, 'rb') as file:
                files = {'document': (os.path.basename(backup_file), file)}
                data = {'chat_id': chat_id, 'caption': caption}
                
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
                
                if response.json().get('ok'):
                    print(f"✅ Backup sent to Telegram: {os.path.basename(backup_file)}")
                    return True
                else:
                    print(f"❌ Telegram API error: {response.json()}")
                    return False
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Telegram connection error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Telegram upload error: {str(e)}")
            return False
    
    def create_backup(self, backup_type="manual"):
        """Create a database backup and send to Telegram"""
        try:
            database_url = self.get_database_url()
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                self.backup_dir, 
                f"hexashop_backup_{backup_type}_{timestamp}.sql"
            )
            
            # Use pg_dump to create backup
            env = os.environ.copy()
            
            # For local PostgreSQL installation
            result = subprocess.run([
                'pg_dump',
                database_url,
                '-f', backup_file,
                '--verbose',
                '--no-password'
            ], capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                print(f"✅ Backup created successfully: {backup_file}")
                
                # Try to send to Telegram
                telegram_sent = self._send_to_telegram(backup_file, backup_type)
                
                # Clean up old backups
                self._cleanup_old_backups()
                
                return {
                    "success": True,
                    "file": backup_file,
                    "size": os.path.getsize(backup_file),
                    "timestamp": timestamp,
                    "type": backup_type,
                    "telegram_sent": telegram_sent
                }
            else:
                print(f"❌ Backup failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            print(f"❌ Backup error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def restore_backup(self, backup_file):
        """Restore database from backup file"""
        try:
            if not os.path.exists(backup_file):
                return {"success": False, "error": "Backup file not found"}
            
            database_url = self.get_database_url()
            
            # Use psql to restore backup
            env = os.environ.copy()
            
            result = subprocess.run([
                'psql',
                database_url,
                '-f', backup_file,
                '--verbose',
                '--no-password'
            ], capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                print(f"✅ Database restored successfully from: {backup_file}")
                return {
                    "success": True,
                    "message": "Database restored successfully"
                }
            else:
                print(f"❌ Restore failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            print(f"❌ Restore error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.sql') and filename.startswith('hexashop_backup_'):
                    filepath = os.path.join(self.backup_dir, filename)
                    stats = os.stat(filepath)
                    
                    # Parse backup type and timestamp from filename
                    parts = filename.replace('hexashop_backup_', '').replace('.sql', '').split('_')
                    backup_type = parts[0]
                    timestamp = '_'.join(parts[1:])
                    
                    backups.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stats.st_size,
                        'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        'type': backup_type,
                        'timestamp': timestamp
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            print(f"❌ Error listing backups: {str(e)}")
            return []
    
    def _cleanup_old_backups(self):
        """Remove old backups beyond the maximum limit"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # Keep only the newest max_backups
                backups_to_delete = backups[self.max_backups:]
                
                for backup in backups_to_delete:
                    os.remove(backup['filepath'])
                    print(f"🗑️ Deleted old backup: {backup['filename']}")
                
                print(f"✅ Cleaned up {len(backups_to_delete)} old backups")
                
        except Exception as e:
            print(f"❌ Error cleaning up backups: {str(e)}")
    
    def schedule_automatic_backups(self):
        """Schedule automatic backups at :00 and :30 of every hour"""
        # Backup at :00 and :30 of every hour (clock-aligned)
        schedule.every().hour.at(":00").do(
            lambda: self.create_backup("auto_30min")
        )
        schedule.every().hour.at(":30").do(
            lambda: self.create_backup("auto_30min")
        )
        
        # Daily backup at 2 AM (as a fallback)
        schedule.every().day.at("02:00").do(
            lambda: self.create_backup("auto_daily")
        )
        
        print("✅ Automatic backups scheduled: At :00 and :30 of every hour + Daily at 02:00")
        print("💾 Backup retention: Last 96 backups (48 hours)")
        print("🤖 Telegram notifications: Enabled" if os.environ.get('TELEGRAM_BOT_TOKEN') else "⚠️ Telegram notifications: Not configured")
        
        # Run scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

# Global backup manager instance
backup_manager = BackupManager()