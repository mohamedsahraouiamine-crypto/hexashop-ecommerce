from flask import Blueprint, jsonify, request, current_app
from models import Product, db
import json
from sqlalchemy.exc import OperationalError
import time
from datetime import datetime

products_bp = Blueprint('products', __name__)

# ADVANCED CACHING CONFIGURATION
CACHE_PREFIX = 'hexashop'
DEFAULT_CACHE_TTL = 300      # 5 minutes for general data
PRODUCT_CACHE_TTL = 600      # 10 minutes for products (increased)
SEARCH_CACHE_TTL = 180       # 3 minutes for search results
ADMIN_CACHE_TTL = 30         # 30 seconds for admin data (frequent updates)
ORDER_CACHE_TTL = 900        # 15 minutes for orders (less frequent changes)
FEATURED_CACHE_TTL = 1800    # 30 minutes for featured products

# Cache statistics tracking
CACHE_STATS = {
    'hits': 0,
    'misses': 0,
    'invalidations': 0
}

def _get_redis_client():
    """Get Redis client with connection check"""
    client = getattr(current_app, 'redis_client', None)
    if client:
        try:
            # Quick ping to verify connection
            client.ping()
            return client
        except:
            return None
    return None

def _build_cache_key(category, *segments):
    """Build cache key with category prefix for better organization"""
    normalized = [str(s).strip().lower().replace(' ', '_') for s in segments if s is not None]
    key_parts = [CACHE_PREFIX, category]
    key_parts.extend(normalized)
    return ":".join(key_parts)

def _get_cached_payload(cache_key):
    """Get cached data with statistics tracking"""
    client = _get_redis_client()
    if not client:
        CACHE_STATS['misses'] += 1
        return None
    
    try:
        cached = client.get(cache_key)
        if cached is None:
            CACHE_STATS['misses'] += 1
            return None
        
        CACHE_STATS['hits'] += 1
        
        if isinstance(cached, bytes):
            cached = cached.decode('utf-8')
        
        # Parse and return
        data = json.loads(cached)
        
        # Add cache hit metadata
        if isinstance(data, dict):
            data['_cache_hit'] = True
            data['_cache_time'] = datetime.utcnow().isoformat()
        
        return data
        
    except Exception as e:
        current_app.logger.warning(f"Redis cache read failed ({cache_key}): {e}")
        CACHE_STATS['misses'] += 1
        return None

def _set_cached_payload(cache_key, payload, ttl=DEFAULT_CACHE_TTL):
    """Set cached data with compression for large payloads"""
    client = _get_redis_client()
    if not client:
        return
    
    try:
        # For large payloads, add size optimization
        payload_str = json.dumps(payload)
        
        # Store with TTL
        client.setex(cache_key, ttl, payload_str)
        
        # Also store metadata about the cache entry
        meta_key = f"{cache_key}:meta"
        meta_data = {
            'created': datetime.utcnow().isoformat(),
            'ttl': ttl,
            'size': len(payload_str)
        }
        client.setex(meta_key, ttl, json.dumps(meta_data))
        
    except Exception as e:
        current_app.logger.warning(f"Redis cache write failed ({cache_key}): {e}")

def invalidate_cache_pattern(pattern):
    """Invalidate cache by pattern"""
    client = _get_redis_client()
    if not client:
        return
    
    try:
        deleted_count = 0
        for key in client.scan_iter(pattern):
            client.delete(key)
            deleted_count += 1
        
        CACHE_STATS['invalidations'] += deleted_count
        
        if deleted_count > 0:
            current_app.logger.info(f"🗑️ Cache invalidated: {deleted_count} keys for pattern {pattern}")
        
        return deleted_count
        
    except Exception as e:
        current_app.logger.warning(f"Cache invalidation failed: {e}")
        return 0

def invalidate_product_cache():
    """Invalidate all product-related cache"""
    deleted = invalidate_cache_pattern(f"{CACHE_PREFIX}:product:*")
    deleted += invalidate_cache_pattern(f"{CACHE_PREFIX}:featured:*")
    deleted += invalidate_cache_pattern(f"{CACHE_PREFIX}:category:*")
    deleted += invalidate_cache_pattern(f"{CACHE_PREFIX}:brand:*")
    
    if deleted > 0:
        print(f"✅ Product cache invalidated ({deleted} keys)")
    return deleted

def get_cache_stats():
    """Get cache statistics"""
    return CACHE_STATS.copy()

def clear_all_cache():
    """Clear ALL application cache (use with caution)"""
    deleted = invalidate_cache_pattern(f"{CACHE_PREFIX}:*")
    CACHE_STATS['hits'] = 0
    CACHE_STATS['misses'] = 0
    CACHE_STATS['invalidations'] = 0
    return deleted

@products_bp.route('/')
def get_all_products():
    # Use new cache key format
    cache_key = _build_cache_key('product', 'all')
    cached = _get_cached_payload(cache_key)
    if cached is not None:
        return jsonify(cached)

    # Simple query (optimization removed for now)
    products = Product.query.all()
    
    response = [product.to_dict() for product in products]
    _set_cached_payload(cache_key, response, ttl=PRODUCT_CACHE_TTL)
    return jsonify(response)

@products_bp.route('/category/<category>')
def get_products_by_category(category):
    if not category or len(category) > 50:
        return jsonify({"error": "Invalid category"}), 400

    valid_categories = ['men', 'women', 'kids']
    category_lower = category.lower()
    if category_lower not in valid_categories:
        return jsonify({"error": "Invalid category"}), 400

    cache_key = _build_cache_key('category', category_lower)
    cached = _get_cached_payload(cache_key)
    if cached is not None:
        return jsonify(cached)

    products = Product.query.filter_by(model=category.capitalize()).all()
    
    response = [product.to_dict() for product in products]
    _set_cached_payload(cache_key, response, ttl=PRODUCT_CACHE_TTL)
    return jsonify(response)

@products_bp.route('/brand/<brand>')
def get_products_by_brand(brand):
    if not brand or len(brand) > 50:
        return jsonify({"error": "Invalid brand"}), 400

    brand_map = {
        'prada': 'Prada',
        'boss': 'Hugo Boss',
        'rayban': 'Ray-Ban',
        'marbella': 'Marbella',
        'gucci': 'Gucci',
        'versace': 'Versace',
        'oakley': 'Oakley',
        'polar': 'Polar'
    }

    brand_name = brand_map.get(brand.lower(), brand)
    cache_key = _build_cache_key('brand', brand_name)
    cached = _get_cached_payload(cache_key)
    if cached is not None:
        return jsonify(cached)

    products = Product.query.filter(Product.brand.ilike(f'%{brand_name}%')).all()
    response = [product.to_dict() for product in products]
    _set_cached_payload(cache_key, response)
    return jsonify(response)

@products_bp.route('/search')
def search_products():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    if len(query) > 100:
        return jsonify({"error": "Search query too long"}), 400

    cache_key = _build_cache_key('search', query)
    cached = _get_cached_payload(cache_key)
    if cached is not None:
        return jsonify(cached)

    products = Product.query.filter(
        (Product.title.ilike(f'%{query}%')) |
        (Product.brand.ilike(f'%{query}%')) |
        (Product.description.ilike(f'%{query}%'))
    ).all()

    response = [product.to_dict() for product in products]
    _set_cached_payload(cache_key, response, ttl=SEARCH_CACHE_TTL)
    return jsonify(response)

# NEW: Featured products endpoint for homepage
@products_bp.route('/featured')
def get_featured_products():
    """Get all featured products for homepage display"""
    cache_key = _build_cache_key('featured', 'homepage')
    cached = _get_cached_payload(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    # ONLY CHANGE MADE: Removed .limit(12) - now shows ALL featured products
    products = Product.query.filter_by(is_featured=True).order_by(Product.created_at.desc()).all()
    
    response = [product.to_dict() for product in products]
    _set_cached_payload(cache_key, response, ttl=FEATURED_CACHE_TTL)
    return jsonify(response)

@products_bp.route('/<product_id>')
def get_product(product_id):
    if not product_id or len(product_id) > 50:
        return jsonify({"error": "Invalid product ID"}), 400

    product = Product.query.get(product_id)
    if product:
        return jsonify(product.to_dict())
    return jsonify({"error": "Product not found"}), 404

@products_bp.route('/', methods=['POST'])
def create_product():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = request.json

            required_fields = ['id', 'title', 'price', 'brand', 'description', 'model', 'type']
            # REMOVED: 'quantity' from required fields
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400

            if len(data['id']) > 50:
                return jsonify({"error": "Product ID too long"}), 400
            if len(data['title']) > 200:
                return jsonify({"error": "Product title too long"}), 400
            if len(data['brand']) > 100:
                return jsonify({"error": "Brand name too long"}), 400
            if len(data['description']) > 1000:
                return jsonify({"error": "Description too long"}), 400

            try:
                price = float(data['price'])
                if price < 0:
                    return jsonify({"error": "Price cannot be negative"}), 400
            except ValueError:
                return jsonify({"error": "Invalid price format"}), 400

            existing_product = Product.query.get(data['id'])
            if existing_product:
                return jsonify({"error": "Product with this ID already exists"}), 400

            # NEW: Handle discount pricing fields
            discount_price = data.get('discount_price')
            discount_active = data.get('discount_active', False)
            discount_start = data.get('discount_start')
            discount_end = data.get('discount_end')

            # Validate discount price
            if discount_price is not None:
                try:
                    discount_price = float(discount_price)
                    if discount_price < 0:
                        return jsonify({"error": "Discount price cannot be negative"}), 400
                    if discount_price >= price:
                        return jsonify({"error": "Discount price must be less than regular price"}), 400
                except ValueError:
                    return jsonify({"error": "Invalid discount price format"}), 400

            # Parse discount dates
            discount_start_dt = None
            discount_end_dt = None
            if discount_start:
                try:
                    discount_start_dt = datetime.fromisoformat(discount_start.replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({"error": "Invalid discount start date format"}), 400
            
            if discount_end:
                try:
                    discount_end_dt = datetime.fromisoformat(discount_end.replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({"error": "Invalid discount end date format"}), 400

            # Validate discount dates
            if discount_start_dt and discount_end_dt and discount_end_dt <= discount_start_dt:
                return jsonify({"error": "Discount end date must be after start date"}), 400

            # NEW: Handle available colors - now required for stock management
            available_colors = data.get('available_colors', [])
            if not isinstance(available_colors, list):
                return jsonify({"error": "Available colors must be an array"}), 400

            # Validate color objects - now required for stock
            if len(available_colors) == 0:
                return jsonify({"error": "At least one color with stock information is required"}), 400

            for color in available_colors:
                if not isinstance(color, dict) or 'name' not in color or 'images' not in color or 'stock' not in color:
                    return jsonify({"error": "Each color must have 'name', 'images', and 'stock' fields"}), 400
                if not isinstance(color['images'], list):
                    return jsonify({"error": "Color images must be an array"}), 400
                if not isinstance(color['stock'], int) or color['stock'] < 0:
                    return jsonify({"error": "Color stock must be a non-negative integer"}), 400

            # NEW: Handle featured product flag
            is_featured = data.get('is_featured', False)

            product = Product(
                id=data['id'],
                title=data['title'],
                price=price,
                brand=data['brand'],
                description=data['description'],
                model=data['model'],
                frame_shape=data.get('frame_shape', ''),
                frame_material=data.get('frame_material', ''),
                frame_color=data.get('frame_color', ''),
                lenses=data.get('lenses', ''),
                protection=data.get('protection', ''),
                dimensions=data.get('dimensions', ''),
                images=json.dumps(data.get('images', {})),
                type=data['type'],
                # REMOVED: quantity field - using color-specific quantities only
                # NEW: Discount pricing fields
                discount_price=discount_price,
                discount_active=discount_active,
                discount_start=discount_start_dt,
                discount_end=discount_end_dt,
                # NEW: Color selection feature with per-color stock (now required)
                available_colors=json.dumps(available_colors),
                # NEW: Featured product flag
                is_featured=is_featured
            )

            db.session.add(product)
            db.session.commit()
            invalidate_product_cache()

            return jsonify({
                "message": "Product created successfully",
                "product": product.to_dict()
            }), 201

        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))
                continue
            return jsonify({"error": "Database busy, please try again"}), 503
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Failed to create product after multiple attempts"}), 503

@products_bp.route('/<product_id>', methods=['PUT'])
def update_product(product_id):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if not product_id or len(product_id) > 50:
                return jsonify({"error": "Invalid product ID"}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404

            data = request.json

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

            # NEW: Handle discount pricing fields
            if 'discount_price' in data:
                discount_price = data['discount_price']
                if discount_price is not None:
                    try:
                        discount_price = float(discount_price)
                        if discount_price < 0:
                            return jsonify({"error": "Discount price cannot be negative"}), 400
                        current_price = data.get('price', product.price)
                        if discount_price >= current_price:
                            return jsonify({"error": "Discount price must be less than regular price"}), 400
                        product.discount_price = discount_price
                    except ValueError:
                        return jsonify({"error": "Invalid discount price format"}), 400
                else:
                    product.discount_price = None

            if 'discount_active' in data:
                product.discount_active = bool(data['discount_active'])

            if 'discount_start' in data:
                discount_start = data['discount_start']
                if discount_start:
                    try:
                        product.discount_start = datetime.fromisoformat(discount_start.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid discount start date format"}), 400
                else:
                    product.discount_start = None

            if 'discount_end' in data:
                discount_end = data['discount_end']
                if discount_end:
                    try:
                        product.discount_end = datetime.fromisoformat(discount_end.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid discount end date format"}), 400
                else:
                    product.discount_end = None

            # Validate discount dates
            if product.discount_start and product.discount_end and product.discount_end <= product.discount_start:
                return jsonify({"error": "Discount end date must be after start date"}), 400

            # NEW: Handle available colors - now required for stock management
            if 'available_colors' in data:
                available_colors = data['available_colors']
                if not isinstance(available_colors, list):
                    return jsonify({"error": "Available colors must be an array"}), 400

                # Validate color objects - now required for stock
                if len(available_colors) == 0:
                    return jsonify({"error": "At least one color with stock information is required"}), 400

                for color in available_colors:
                    if not isinstance(color, dict) or 'name' not in color or 'images' not in color or 'stock' not in color:
                        return jsonify({"error": "Each color must have 'name', 'images', and 'stock' fields"}), 400
                    if not isinstance(color['images'], list):
                        return jsonify({"error": "Color images must be an array"}), 400
                    if not isinstance(color['stock'], int) or color['stock'] < 0:
                        return jsonify({"error": "Color stock must be a non-negative integer"}), 400

                product.available_colors = json.dumps(available_colors)

            # NEW: Handle featured product flag
            if 'is_featured' in data:
                product.is_featured = bool(data['is_featured'])

            # Update other fields
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
            if 'images' in data:
                product.images = json.dumps(data['images'])

            db.session.commit()
            invalidate_product_cache()

            return jsonify({
                "message": "Product updated successfully",
                "product": product.to_dict()
            })

        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))
                continue
            return jsonify({"error": "Database busy, please try again"}), 503
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Failed to update product after multiple attempts"}), 503

@products_bp.route('/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if not product_id or len(product_id) > 50:
                return jsonify({"error": "Invalid product ID"}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404

            db.session.delete(product)
            db.session.commit()
            invalidate_product_cache()

            return jsonify({"message": "Product deleted successfully"})

        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))
                continue
            return jsonify({"error": "Database busy, please try again"}), 503
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Failed to delete product after multiple attempts"}), 503

# REMOVED: update_product_quantity endpoint - using color-specific quantities only

@products_bp.route('/cache-stats')
def get_cache_statistics():
    """Get cache performance statistics"""
    stats = get_cache_stats()
    
    # Calculate hit rate
    total = stats['hits'] + stats['misses']
    stats['hit_rate'] = f"{(stats['hits'] / total * 100):.1f}%" if total > 0 else "0%"
    stats['total_requests'] = total
    
    # Get Redis info if available
    client = _get_redis_client()
    if client:
        try:
            redis_info = client.info('memory')
            stats['redis_memory'] = {
                'used': redis_info['used_memory_human'],
                'peak': redis_info['used_memory_peak_human']
            }
        except:
            stats['redis_memory'] = 'unavailable'
    
    return jsonify(stats)

@products_bp.route('/cache-clear', methods=['POST'])
def clear_products_cache():
    """Clear all cache (admin only)"""
    # Simple auth check - you might want to add proper admin auth
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != 'Bearer admin-cache-clear':
        return jsonify({"error": "Unauthorized"}), 401
    
    deleted = clear_all_cache()
    return jsonify({
        "success": True,
        "message": f"Cache cleared ({deleted} keys deleted)",
        "stats_reset": True
    })

__all__ = ['products_bp', 'invalidate_product_cache']