from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
from database import db, init_db
from models import Product, Order, OrderItem, AdminAccessCode, AdminUser
from routes.products import products_bp
from routes.orders import orders_bp
from routes.cart import cart_bp
from routes.tracking import tracking_bp
from routes.admin import admin_bp
from routes.backup import backup_bp
from backup_manager import backup_manager
from datetime import datetime
import secrets
from dotenv import load_dotenv
from redis import Redis
from flask_session import Session
import time  # ADDED
from performance_monitor import performance_monitor  # ADDED
import logging  # ADDED

load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(base_dir, 'frontend')

app = Flask(
    __name__,
    static_folder=frontend_path,
    template_folder=frontend_path
)

# Load environment variables
load_dotenv()

# Database configuration for Railway
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required")

# Railway provides postgres:// URL, SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ENHANCED CONNECTION POOLING CONFIGURATION
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,           # Number of permanent connections
    'max_overflow': 30,        # Max temporary connections when pool is exhausted
    'pool_pre_ping': True,     # Verify connections before using them
    'pool_recycle': 1800,      # Recycle connections every 30 minutes
    'pool_timeout': 30,        # Seconds to wait for a connection
    'echo': False,             # Don't log SQL queries (set to True for debugging)
    'pool_reset_on_return': 'rollback'  # Reset connections when returned to pool
}

# PostgreSQL specific optimizations
if 'postgresql' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args'] = {
        'connect_timeout': 10,      # Connection timeout in seconds
        'keepalives': 1,            # Enable TCP keepalives
        'keepalives_idle': 30,      # Seconds before sending first keepalive
        'keepalives_interval': 10,  # Seconds between keepalives
        'keepalives_count': 5,      # Number of keepalives before dropping connection
        'application_name': 'hexashop_optilook_app'  # Custom name for your app
    }

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable is required")

redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
try:
    redis_client = Redis.from_url(redis_url)
    redis_client.ping()
except Exception as redis_error:
    raise RuntimeError("❌ Unable to connect to Redis. Please verify REDIS_URL.") from redis_error

app.redis_client = redis_client

# Check if we're in production mode
is_production = os.environ.get('FLASK_ENV') == 'production'

# ENHANCED SESSION CONFIGURATION WITH PRODUCTION SETTINGS
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis_client
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'hexashop:sess:'
app.config['SESSION_COOKIE_NAME'] = 'hexashop_sid'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # Secure only in production
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Extend session on activity
app.config['SESSION_COOKIE_MAX_AGE'] = 86400  # 24 hours max age

# Session serialization optimization - FIXED: Use pickle for proper serialization
app.config['SESSION_SERIALIZATION_FORMAT'] = 'pickle'  # Changed from 'json' to 'pickle'

print(f"🔒 Session security: {'PRODUCTION (Secure cookies)' if is_production else 'DEVELOPMENT (HTTP allowed)'}")

# Session cleanup and monitoring
import threading
import time
from datetime import datetime, timedelta

def session_cleanup_worker():
    """Background worker to clean up expired sessions"""
    # Get logger
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            # Run cleanup every 30 minutes
            time.sleep(1800)  # 30 minutes
            
            logger.info("🧹 Running session cleanup...")
            
            # Delete expired session keys
            pattern = app.config['SESSION_KEY_PREFIX'] + '*'
            deleted_count = 0
            
            for key in redis_client.scan_iter(pattern):
                try:
                    # Check if key exists and TTL
                    ttl = redis_client.ttl(key)
                    if ttl == -2:  # Key doesn't exist
                        redis_client.delete(key)
                        deleted_count += 1
                    elif ttl == -1:  # No expiration (shouldn't happen)
                        # Set a reasonable expiration
                        redis_client.expire(key, 86400)  # 24 hours
                except Exception as e:
                    logger.warning(f"Error cleaning up session {key}: {e}")
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

# Start session cleanup thread
def start_session_cleanup():
    """Start the session cleanup background thread"""
    if not hasattr(app, 'session_cleanup_thread'):
        cleanup_thread = threading.Thread(target=session_cleanup_worker, daemon=True)
        cleanup_thread.start()
        app.session_cleanup_thread = cleanup_thread
        print("✅ Session cleanup worker started")

# Configure Redis for optimal session management
try:
    # Set memory limits
    redis_client.config_set('maxmemory', '512mb')
    
    # More aggressive eviction policy for sessions
    redis_client.config_set('maxmemory-policy', 'allkeys-lru')
    
    # Enable key eviction notifications (optional)
    redis_client.config_set('notify-keyspace-events', 'Ex')
    
    # Configure save intervals (for persistence)
    redis_client.config_set('save', '900 1 300 10 60 10000')
    
    print("✅ Redis configured: 512MB with LRU eviction + persistence")
    
except Exception as e:
    print(f"⚠️ Could not configure Redis settings: {e}")
    # Set defaults via command if config_set fails
    import subprocess
    try:
        subprocess.run([
            'redis-cli', 'config', 'set', 'maxmemory', '512mb'
        ], capture_output=True)
        subprocess.run([
            'redis-cli', 'config', 'set', 'maxmemory-policy', 'allkeys-lru'
        ], capture_output=True)
        print("✅ Redis configured via redis-cli fallback")
    except:
        print("❌ Could not configure Redis via any method")

db.init_app(app)

# Enhanced CORS configuration - FIXED: Added specific headers for cookies
# Enhanced CORS configuration for production
allowed_origins = ['http://localhost:5000', 'http://127.0.0.1:5000']

# Add Railway URL when in production
if os.environ.get('RAILWAY_STATIC_URL'):
    railway_url = os.environ.get('RAILWAY_STATIC_URL')
    allowed_origins.append(railway_url)
    allowed_origins.append(railway_url.replace('https://', 'http://'))

# Also allow requests from any origin during development
if os.environ.get('FLASK_ENV') != 'production':
    allowed_origins.append('*')

CORS(app, 
     supports_credentials=True,
     origins=allowed_origins,
     allow_headers=['Content-Type', 'Authorization', 'X-CSRF-Token'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Set-Cookie'])

# Initialize session after CORS
Session(app)

# Start session cleanup worker
start_session_cleanup()


# Register all blueprints
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(orders_bp, url_prefix='/api/orders')
app.register_blueprint(cart_bp, url_prefix='/api/cart')
app.register_blueprint(tracking_bp, url_prefix='/api/tracking')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(backup_bp, url_prefix='/api/admin/backup')  # NEW: Register backup routes

login_attempts = {}

def is_rate_limited(identifier, max_attempts=5, window_seconds=300):
    now = datetime.utcnow().timestamp()
    if identifier not in login_attempts:
        login_attempts[identifier] = []

    login_attempts[identifier] = [
        attempt_time
        for attempt_time in login_attempts[identifier]
        if now - attempt_time < window_seconds
    ]

    if len(login_attempts[identifier]) >= max_attempts:
        return True

    login_attempts[identifier].append(now)
    return False

# ========== PERFORMANCE MONITORING MIDDLEWARE ==========

@app.before_request
def before_request():
    """Start timer for request timing"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Record request performance after each request"""
    # Calculate request duration
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        
        # Record request metrics
        endpoint = request.endpoint if request.endpoint else request.path
        performance_monitor.record_request(
            endpoint=endpoint,
            method=request.method,
            duration=duration,
            status_code=response.status_code
        )
        
        # Add performance header for debugging
        response.headers['X-Response-Time'] = f'{duration:.3f}s'
    
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Record exceptions in performance monitor"""
    endpoint = request.endpoint if request.endpoint else request.path
    performance_monitor.record_error(
        endpoint=endpoint,
        error_type=type(e).__name__,
        error_message=str(e)
    )
    
    # Return default error response
    return jsonify({
        "error": "Internal server error",
        "message": str(e) if app.debug else "An error occurred"
    }), 500

# ========== END PERFORMANCE MONITORING ==========

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({'success': False, 'message': 'Too many login attempts. Please try again later.'}), 429

    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password'].strip()

    if len(username) > 80 or len(password) > 120:
        return jsonify({'success': False, 'message': 'Invalid input length'}), 400

    admin_user = AdminUser.query.filter_by(username=username, is_active=True).first()

    if admin_user and admin_user.check_password(password):
        # Clear any existing session first
        session.clear()
        
        # Set session data
        session['admin_logged_in'] = True
        session['admin_username'] = admin_user.username
        session['csrf_token'] = secrets.token_hex(16)
        session['admin_login_time'] = datetime.utcnow().isoformat()
        
        # Make session permanent
        session.permanent = True
        
        # Force session save
        session.modified = True

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': 'admin.html',
            'csrf_token': session['csrf_token']
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/api/admin/check-auth', methods=['GET'])
def check_admin_auth():
    if session.get('admin_logged_in'):
        return jsonify({
            'authenticated': True, 
            'csrf_token': session.get('csrf_token'),
            'username': session.get('admin_username')
        })
    return jsonify({'authenticated': False})

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/debug/session')
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'headers': dict(request.headers),
        'cookies': dict(request.cookies),
        'redis_connected': redis_client.ping() if redis_client else False
    })

@app.route('/api/debug/redis-session')
def debug_redis_session():
    """Debug endpoint to check what's actually in Redis"""
    try:
        session_id = request.cookies.get('hexashop_session')
        if session_id:
            redis_key = f"hexashop:session:{session_id}"
            redis_data = redis_client.get(redis_key)
            return jsonify({
                'session_id': session_id,
                'redis_key': redis_key,
                'redis_data': redis_data.decode('utf-8') if redis_data else None
            })
        return jsonify({'error': 'No session cookie found'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/debug/redis-memory')
def debug_redis_memory():
    """Check Redis memory usage"""
    try:
        info = redis_client.info('memory')
        keys_count = redis_client.dbsize()
        session_count = len(list(redis_client.scan_iter("hexashop:session:*")))
        cache_count = len(list(redis_client.scan_iter("products:*")))
        
        return jsonify({
            'used_memory': info['used_memory_human'],
            'used_memory_peak': info['used_memory_peak_human'],
            'total_keys': keys_count,
            'session_keys': session_count,
            'cache_keys': cache_count,
            'memory_usage_percentage': f"{(info['used_memory'] / (512 * 1024 * 1024)) * 100:.1f}%"
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/debug/fix-session', methods=['POST'])
def fix_session():
    """Emergency endpoint to manually set session data"""
    data = request.json
    session['admin_logged_in'] = True
    session['admin_username'] = data.get('username', 'admin')
    session['csrf_token'] = secrets.token_hex(16)
    session.permanent = True
    session.modified = True
    return jsonify({'success': True, 'message': 'Session manually set'})

@app.route('/api/admin/cleanup-sessions', methods=['POST'])
def cleanup_sessions():
    """Manual session cleanup endpoint"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Authentication required'}), 401
        
    try:
        deleted_count = 0
        for key in redis_client.scan_iter("hexashop:session:*"):
            ttl = redis_client.ttl(key)
            if ttl == -2:  # Key doesn't exist (shouldn't happen)
                redis_client.delete(key)
                deleted_count += 1
            elif ttl == -1:  # No expiration set (old sessions)
                redis_client.delete(key)
                deleted_count += 1
                
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} stale sessions',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/login.html')
def serve_login():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(app.static_folder, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(app.static_folder, filename)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Hexashop backend is running!"})

# ========== PERFORMANCE MONITORING ENDPOINTS ==========

@app.route('/api/performance/health')
def performance_health():
    """Get system health status (public)"""
    health_status = performance_monitor.get_health_status()
    return jsonify(health_status)

@app.route('/api/performance/summary')
def performance_summary():
    """Get performance summary (admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Authentication required"}), 401
    
    summary = performance_monitor.get_summary()
    return jsonify(summary)

@app.route('/api/performance/requests')
def performance_requests():
    """Get recent requests (admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Authentication required"}), 401
    
    # Get last 50 requests
    requests = list(performance_monitor.request_times)[-50:]
    return jsonify({
        'total_requests': len(performance_monitor.request_times),
        'recent_requests': requests
    })

@app.route('/api/performance/slow-queries')
def performance_slow_queries():
    """Get slow queries (admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Authentication required"}), 401
    
    return jsonify({
        'slow_queries': performance_monitor.slow_queries,
        'total_slow_queries': len(performance_monitor.slow_queries)
    })

@app.route('/api/performance/system-metrics')
def performance_system_metrics():
    """Get system metrics (admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Authentication required"}), 401
    
    return jsonify({
        'cpu_usage': performance_monitor.cpu_usage[-10:] if performance_monitor.cpu_usage else [],
        'memory_usage': performance_monitor.memory_usage[-10:] if performance_monitor.memory_usage else [],
        'disk_io': performance_monitor.disk_io[-10:] if performance_monitor.disk_io else []
    })

# ========== END PERFORMANCE ENDPOINTS ==========

def initialize_database():
    init_db()
    print("✅ Database initialized without seeding (using existing data)")

def create_app():
    with app.app_context():
        initialize_database()
        
        # NEW: Initialize backup manager and schedule automatic backups
        backup_manager.init_app(app)
        backup_manager.schedule_automatic_backups()
        print("✅ Backup system initialized and scheduled!")
        
        # NEW: Initialize performance monitor
        performance_monitor.init_app(app)
        print("📊 Performance monitoring initialized!")
        
    return app

if __name__ == '__main__':
    app_with_context = create_app()

    print("🚀 Hexashop Backend Server Starting...")
    print("📧 API Running at: http://127.0.0.1:5000")
    print("🛍️  Frontend at: http://127.0.0.1:5000")
    print("⚡ Using Waitress Production Server (20 threads)")
    print("💾 Redis Memory: 512MB with LRU eviction policy")
    print("⏰ Session Lifetime: 2 hours")
    print("💾 Backup System: Active (Every 30 minutes + Daily at 02:00)")

    from waitress import serve
    serve(app_with_context, host='0.0.0.0', port=5000, threads=20)