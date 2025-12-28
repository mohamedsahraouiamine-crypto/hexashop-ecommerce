"""
Backup API Routes for Hexashop Admin
"""
from flask import Blueprint, jsonify, request, send_file
import os
from backup_manager import backup_manager

backup_bp = Blueprint('backup', __name__)

# Authentication decorator (same as your admin routes)
def admin_required(f):
    def decorated_function(*args, **kwargs):
        from flask import session
        if not session.get('admin_logged_in'):
            return jsonify({"error": "Authentication required"}), 401
        
        # CSRF protection
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token = request.headers.get('X-CSRF-Token') or request.json.get('csrf_token')
            if not csrf_token or csrf_token != session.get('csrf_token'):
                return jsonify({"error": "CSRF token validation failed"}), 403
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@backup_bp.route('/create', methods=['POST'])
@admin_required
def create_backup():
    """Create a manual database backup"""
    try:
        result = backup_manager.create_backup("manual")
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@backup_bp.route('/list', methods=['GET'])
@admin_required
def list_backups():
    """List all available backups"""
    try:
        backups = backup_manager.list_backups()
        return jsonify({
            "success": True,
            "backups": backups,
            "total": len(backups)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@backup_bp.route('/restore', methods=['POST'])
@admin_required
def restore_backup():
    """Restore database from a backup file"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({
                "success": False,
                "error": "Filename is required"
            }), 400
        
        backup_file = os.path.join(backup_manager.backup_dir, filename)
        result = backup_manager.restore_backup(backup_file)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@backup_bp.route('/download/<filename>', methods=['GET'])
@admin_required
def download_backup(filename):
    """Download a backup file"""
    try:
        backup_file = os.path.join(backup_manager.backup_dir, filename)
        
        if not os.path.exists(backup_file):
            return jsonify({
                "success": False,
                "error": "Backup file not found"
            }), 404
        
        return send_file(
            backup_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@backup_bp.route('/delete/<filename>', methods=['DELETE'])
@admin_required
def delete_backup(filename):
    """Delete a backup file"""
    try:
        backup_file = os.path.join(backup_manager.backup_dir, filename)
        
        if not os.path.exists(backup_file):
            return jsonify({
                "success": False,
                "error": "Backup file not found"
            }), 404
        
        os.remove(backup_file)
        
        return jsonify({
            "success": True,
            "message": f"Backup {filename} deleted successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@backup_bp.route('/cleanup', methods=['POST'])
@admin_required
def cleanup_backups():
    """Manually trigger backup cleanup"""
    try:
        backup_manager._cleanup_old_backups()
        return jsonify({
            "success": True,
            "message": "Backup cleanup completed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500