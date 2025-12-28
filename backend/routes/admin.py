from flask import Blueprint, jsonify, request, session, current_app
from models import Order, OrderItem, Product, db, AdminAccessCode, PromoCode
from datetime import datetime
import json

admin_bp = Blueprint('admin', __name__)

# Authentication decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"error": "Authentication required"}), 401
        
        # CSRF protection for state-changing operations
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token = request.headers.get('X-CSRF-Token') or request.json.get('csrf_token')
            if not csrf_token or csrf_token != session.get('csrf_token'):
                return jsonify({"error": "CSRF token validation failed"}), 403
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Get all orders for admin
@admin_bp.route('/orders')
@admin_required
def get_all_orders():
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update order status
@admin_bp.route('/orders/<order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    try:
        # Input validation
        if not order_id or len(order_id) > 20:
            return jsonify({"error": "Invalid order ID"}), 400
            
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        new_status = request.json.get('status')
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({"error": "Invalid status"}), 400
        
        order.status = new_status
        
        # Add tracking update
        updates = []
        if order.delivery_updates:
            updates = json.loads(order.delivery_updates)
        
        status_messages = {
            'pending': 'Order received',
            'confirmed': 'Order confirmed and processing',
            'shipped': 'Order shipped to delivery service', 
            'delivered': 'Order delivered successfully'
        }
        
        updates.append({
            'date': datetime.utcnow().isoformat(),
            'status': new_status,
            'message': status_messages.get(new_status, 'Status updated')
        })
        
        order.delivery_updates = json.dumps(updates)
        db.session.commit()
        
        return jsonify({"message": "Order status updated", "order": order.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Delete order
@admin_bp.route('/orders/<order_id>', methods=['DELETE'])
@admin_required
def delete_order(order_id):
    try:
        # Input validation
        if not order_id or len(order_id) > 20:
            return jsonify({"error": "Invalid order ID"}), 400
            
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Delete all items associated with this order first
        OrderItem.query.filter_by(order_id=order.id).delete()
        
        # Delete the order itself
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({"message": "Order deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting order: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get dashboard stats
@admin_bp.route('/stats')
@admin_required
def get_dashboard_stats():
    try:
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        total_revenue = db.session.query(db.func.sum(Order.total)).scalar() or 0
        total_products = Product.query.count()
        
        return jsonify({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'total_products': total_products
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NEW: Get system memory stats
@admin_bp.route('/system-stats')
@admin_required
def get_system_stats():
    try:
        redis_client = current_app.redis_client
        if not redis_client:
            return jsonify({"error": "Redis not available"}), 500
            
        # Get Redis memory info
        info = redis_client.info('memory')
        keys_count = redis_client.dbsize()
        session_count = len(list(redis_client.scan_iter("hexashop:session:*")))
        cache_count = len(list(redis_client.scan_iter("products:*")))
        
        # Calculate memory usage percentage (512MB limit)
        memory_used_mb = info['used_memory'] / (1024 * 1024)
        memory_percentage = (memory_used_mb / 512) * 100
        
        return jsonify({
            'redis_memory': {
                'used_memory': info['used_memory_human'],
                'used_memory_peak': info['used_memory_peak_human'],
                'memory_usage_percentage': f"{memory_percentage:.1f}%",
                'memory_status': '✅ Optimal' if memory_percentage < 70 else '⚠️ High' if memory_percentage < 90 else '🚨 Critical'
            },
            'keys_count': {
                'total_keys': keys_count,
                'sessions': session_count,
                'cache_entries': cache_count
            },
            'session_settings': {
                'lifetime_hours': 2,
                'max_memory': '512MB'
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Validate admin access code - REMOVE @admin_required for this endpoint
@admin_bp.route('/validate-admin-code', methods=['POST'])
def validate_admin_code():  # ← REMOVED THE @admin_required LINE
    try:
        data = request.json
        code = data.get('code', '').strip()
        
        # Input validation
        if not code or len(code) > 100:
            return jsonify({"error": "Invalid code"}), 400
        
        # Check if code exists and is active
        admin_code = AdminAccessCode.query.filter_by(code=code, is_active=True).first()
        
        if admin_code:
            return jsonify({
                "valid": True,
                "message": "Admin access granted"
            })
        else:
            return jsonify({
                "valid": False,
                "message": "Invalid admin access code"
            }), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all admin codes (for admin management)
@admin_bp.route('/admin-codes')
@admin_required
def get_admin_codes():
    try:
        codes = AdminAccessCode.query.all()
        return jsonify([code.to_dict() for code in codes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create new admin code
@admin_bp.route('/admin-codes', methods=['POST'])
@admin_required
def create_admin_code():
    try:
        data = request.json
        code = data.get('code', '').strip()
        
        if not code or len(code) > 100:
            return jsonify({"error": "Code is required and must be less than 100 characters"}), 400
        
        # Check if code already exists
        existing_code = AdminAccessCode.query.filter_by(code=code).first()
        if existing_code:
            return jsonify({"error": "Code already exists"}), 400
        
        admin_code = AdminAccessCode(code=code)
        db.session.add(admin_code)
        db.session.commit()
        
        return jsonify({
            "message": "Admin code created successfully",
            "code": admin_code.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Deactivate admin code
@admin_bp.route('/admin-codes/<code_id>/deactivate', methods=['PUT'])
@admin_required
def deactivate_admin_code(code_id):
    try:
        # Input validation
        if not code_id or not code_id.isdigit():
            return jsonify({"error": "Invalid code ID"}), 400
            
        admin_code = AdminAccessCode.query.get(code_id)
        if not admin_code:
            return jsonify({"error": "Admin code not found"}), 404
        
        admin_code.is_active = False
        db.session.commit()
        
        return jsonify({"message": "Admin code deactivated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Get all products for admin
@admin_bp.route('/products')
@admin_required
def get_all_products():
    try:
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update product
@admin_bp.route('/products/<product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    try:
        # Input validation
        if not product_id or len(product_id) > 50:
            return jsonify({"error": "Invalid product ID"}), 400
            
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        data = request.json
        
        # Input validation for each field
        if 'title' in data and len(data['title']) > 200:
            return jsonify({"error": "Title too long"}), 400
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    return jsonify({"error": "Price cannot be negative"}), 400
            except ValueError:
                return jsonify({"error": "Invalid price format"}), 400
        if 'brand' in data and len(data['brand']) > 100:
            return jsonify({"error": "Brand name too long"}), 400
        if 'description' in data and len(data['description']) > 1000:
            return jsonify({"error": "Description too long"}), 400
        if 'quantity' in data:
            try:
                quantity = int(data['quantity'])
                if quantity < 0:
                    return jsonify({"error": "Quantity cannot be negative"}), 400
            except ValueError:
                return jsonify({"error": "Invalid quantity format"}), 400
        
        # Update fields
        if 'title' in data:
            product.title = data['title']
        if 'price' in data:
            product.price = float(data['price'])
        if 'brand' in data:
            product.brand = data['brand']
        if 'description' in data:
            product.description = data['description']
        if 'model' in data:
            product.model = data['model']
        if 'frame_shape' in data:
            product.frame_shape = data['frame_shape']
        if 'frame_material' in data:
            product.frame_material = data['frame_material']
        if 'frame_color' in data:
            product.frame_color = data['frame_color']
        if 'lenses' in data:
            product.lenses = data['lenses']
        if 'protection' in data:
            product.protection = data['protection']
        if 'dimensions' in data:
            product.dimensions = data['dimensions']
        if 'type' in data:
            product.type = data['type']
        if 'quantity' in data:
            product.quantity = int(data['quantity'])
        
        db.session.commit()
        
        return jsonify({
            "message": "Product updated successfully",
            "product": product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Delete product
@admin_bp.route('/products/<product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    try:
        # Input validation
        if not product_id or len(product_id) > 50:
            return jsonify({"error": "Invalid product ID"}), 400
            
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({"message": "Product deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ========== PROMO CODE MANAGEMENT ROUTES ==========

# Get all promo codes
@admin_bp.route('/promo-codes')
@admin_required
def get_all_promo_codes():
    try:
        promo_codes = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
        return jsonify([promo.to_dict() for promo in promo_codes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create new promo code
@admin_bp.route('/promo-codes', methods=['POST'])
@admin_required
def create_promo_code():
    try:
        data = request.json
        
        # Input validation
        required_fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_until']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        code = data['code'].strip().upper()
        if not code or len(code) > 50:
            return jsonify({"error": "Code is required and must be less than 50 characters"}), 400
        
        # Check if code already exists
        existing_promo = PromoCode.query.filter_by(code=code).first()
        if existing_promo:
            return jsonify({"error": "Promo code already exists"}), 400
        
        # Validate discount type
        if data['discount_type'] not in ['percentage', 'fixed']:
            return jsonify({"error": "Discount type must be 'percentage' or 'fixed'"}), 400
        
        # Validate discount value
        try:
            discount_value = float(data['discount_value'])
            if discount_value <= 0:
                return jsonify({"error": "Discount value must be positive"}), 400
            if data['discount_type'] == 'percentage' and discount_value > 100:
                return jsonify({"error": "Percentage discount cannot exceed 100%"}), 400
        except ValueError:
            return jsonify({"error": "Invalid discount value"}), 400
        
        # Parse dates
        try:
            valid_from = datetime.fromisoformat(data['valid_from'].replace('Z', '+00:00'))
            valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00'))
            
            if valid_until <= valid_from:
                return jsonify({"error": "Valid until date must be after valid from date"}), 400
        except ValueError:
            return jsonify({"error": "Invalid date format. Use ISO format (e.g., 2024-01-01T00:00:00Z)"}), 400
        
        # Create promo code
        promo_code = PromoCode(
            code=code,
            discount_type=data['discount_type'],
            discount_value=discount_value,
            min_order_amount=data.get('min_order_amount', 0.0),
            max_discount=data.get('max_discount'),
            usage_limit=data.get('usage_limit'),
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(promo_code)
        db.session.commit()
        
        return jsonify({
            "message": "Promo code created successfully",
            "promo_code": promo_code.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Update promo code
@admin_bp.route('/promo-codes/<int:promo_id>', methods=['PUT'])
@admin_required
def update_promo_code(promo_id):
    try:
        promo_code = PromoCode.query.get(promo_id)
        if not promo_code:
            return jsonify({"error": "Promo code not found"}), 404
        
        data = request.json
        
        # Update fields if provided
        if 'code' in data:
            new_code = data['code'].strip().upper()
            if new_code != promo_code.code:
                existing = PromoCode.query.filter_by(code=new_code).first()
                if existing and existing.id != promo_id:
                    return jsonify({"error": "Promo code already exists"}), 400
                promo_code.code = new_code
        
        if 'discount_type' in data:
            if data['discount_type'] not in ['percentage', 'fixed']:
                return jsonify({"error": "Discount type must be 'percentage' or 'fixed'"}), 400
            promo_code.discount_type = data['discount_type']
        
        if 'discount_value' in data:
            try:
                discount_value = float(data['discount_value'])
                if discount_value <= 0:
                    return jsonify({"error": "Discount value must be positive"}), 400
                if promo_code.discount_type == 'percentage' and discount_value > 100:
                    return jsonify({"error": "Percentage discount cannot exceed 100%"}), 400
                promo_code.discount_value = discount_value
            except ValueError:
                return jsonify({"error": "Invalid discount value"}), 400
        
        if 'min_order_amount' in data:
            promo_code.min_order_amount = float(data['min_order_amount'])
        
        if 'max_discount' in data:
            promo_code.max_discount = float(data['max_discount']) if data['max_discount'] is not None else None
        
        if 'usage_limit' in data:
            promo_code.usage_limit = int(data['usage_limit']) if data['usage_limit'] is not None else None
        
        if 'valid_from' in data:
            try:
                promo_code.valid_from = datetime.fromisoformat(data['valid_from'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid valid_from date format"}), 400
        
        if 'valid_until' in data:
            try:
                promo_code.valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid valid_until date format"}), 400
        
        if 'is_active' in data:
            promo_code.is_active = bool(data['is_active'])
        
        # Validate dates
        if promo_code.valid_until <= promo_code.valid_from:
            return jsonify({"error": "Valid until date must be after valid from date"}), 400
        
        db.session.commit()
        
        return jsonify({
            "message": "Promo code updated successfully",
            "promo_code": promo_code.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Delete promo code
@admin_bp.route('/promo-codes/<int:promo_id>', methods=['DELETE'])
@admin_required
def delete_promo_code(promo_id):
    try:
        promo_code = PromoCode.query.get(promo_id)
        if not promo_code:
            return jsonify({"error": "Promo code not found"}), 404
        
        db.session.delete(promo_code)
        db.session.commit()
        
        return jsonify({"message": "Promo code deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Toggle promo code status
@admin_bp.route('/promo-codes/<int:promo_id>/toggle', methods=['PUT'])
@admin_required
def toggle_promo_code(promo_id):
    try:
        promo_code = PromoCode.query.get(promo_id)
        if not promo_code:
            return jsonify({"error": "Promo code not found"}), 404
        
        promo_code.is_active = not promo_code.is_active
        db.session.commit()
        
        action = "activated" if promo_code.is_active else "deactivated"
        return jsonify({
            "message": f"Promo code {action} successfully",
            "promo_code": promo_code.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500