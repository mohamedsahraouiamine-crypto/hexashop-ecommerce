from database import db
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash

class Product(db.Model):
    __table_args__ = (
        # Performance indexes
        db.Index('idx_product_model', 'model'),
        db.Index('idx_product_brand', 'brand'),
        db.Index('idx_product_type', 'type'),
        db.Index('idx_product_featured', 'is_featured'),
        db.Index('idx_product_discount', 'discount_active', 'discount_end'),
        db.Index('idx_product_created', 'created_at'),
        # Composite indexes for common queries
        db.Index('idx_product_model_featured', 'model', 'is_featured'),
        db.Index('idx_product_brand_model', 'brand', 'model'),
    )
    
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(50), nullable=False)  # 'Men', 'Women', 'Kids'
    frame_shape = db.Column(db.String(100))
    frame_material = db.Column(db.String(100))
    frame_color = db.Column(db.String(100))
    lenses = db.Column(db.String(200))
    protection = db.Column(db.String(200))
    dimensions = db.Column(db.String(50))
    images = db.Column(db.Text)  # JSON string of images
    type = db.Column(db.String(50))  # 'sunglasses', 'eyeglasses'
    # REMOVED: quantity field - now using color-specific quantities only
    # NEW: Discount pricing fields
    discount_price = db.Column(db.Float, default=None)  # Discounted price when active
    discount_active = db.Column(db.Boolean, default=False)  # Whether discount is active
    discount_start = db.Column(db.DateTime, default=None)  # When discount starts
    discount_end = db.Column(db.DateTime, default=None)  # When discount ends
    # NEW: Color selection feature with per-color stock
    available_colors = db.Column(db.Text, default='[]')  # JSON array of color objects with stock
    # NEW: Featured product flag for homepage display
    is_featured = db.Column(db.Boolean, default=False)  # Whether product is featured on homepage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'brand': self.brand,
            'description': self.description,
            'model': self.model,
            'frame_shape': self.frame_shape,
            'frame_material': self.frame_material,
            'frame_color': self.frame_color,
            'lenses': self.lenses,
            'protection': self.protection,
            'dimensions': self.dimensions,
            'images': json.loads(self.images) if self.images else {},
            'type': self.type,
            # REMOVED: quantity field
            # NEW: Discount pricing fields
            'discount_price': self.discount_price,
            'discount_active': self.discount_active,
            'discount_start': self.discount_start.isoformat() if self.discount_start else None,
            'discount_end': self.discount_end.isoformat() if self.discount_end else None,
            'has_active_discount': self.has_active_discount(),
            # NEW: Color selection feature with per-color stock
            'available_colors': json.loads(self.available_colors) if self.available_colors else [],
            # NEW: Calculate total quantity from color stocks only
            'total_quantity': self.get_total_quantity(),
            # NEW: Featured product flag
            'is_featured': self.is_featured
        }
    
    def has_active_discount(self):
        """Check if product has an active discount"""
        if not self.discount_active or not self.discount_price:
            return False
        
        now = datetime.utcnow()
        
        # Check if discount period is valid
        if self.discount_start and self.discount_end:
            return self.discount_start <= now <= self.discount_end
        
        # If no dates set, just check if active flag is True
        return self.discount_active
    
    def get_current_price(self):
        """Get the current active price (discount or regular)"""
        if self.has_active_discount():
            return self.discount_price
        return self.price
    
    def get_color_stock(self, color_name):
        """Get stock quantity for a specific color"""
        if not self.available_colors:
            return 0
        
        colors = json.loads(self.available_colors)
        for color in colors:
            if color.get('name') == color_name:
                return color.get('stock', 0)
        return 0
    
    def get_total_quantity(self):
        """Calculate total quantity from all color stocks only"""
        if not self.available_colors:
            return 0
        
        colors = json.loads(self.available_colors)
        total = 0
        for color in colors:
            total += color.get('stock', 0)
        return total
    
    def update_color_stock(self, color_name, new_stock):
        """Update stock for a specific color"""
        if not self.available_colors:
            return False
        
        colors = json.loads(self.available_colors)
        for color in colors:
            if color.get('name') == color_name:
                color['stock'] = new_stock
                self.available_colors = json.dumps(colors)
                # REMOVED: No longer update product-level quantity
                return True
        return False

class Order(db.Model):
    __table_args__ = (
        # Performance indexes for order queries
        db.Index('idx_order_phone', 'phone_number'),
        db.Index('idx_order_status', 'status'),
        db.Index('idx_order_created', 'created_at'),
        db.Index('idx_order_status_created', 'status', 'created_at'),
        db.Index('idx_order_phone_created', 'phone_number', 'created_at'),
    )
    
    id = db.Column(db.String(20), primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    wilaya = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    delivery_updates = db.Column(db.Text)  # JSON string of tracking updates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'orderId': self.id,
            'phoneNumber': self.phone_number,
            'customerName': self.customer_name,
            'wilaya': self.wilaya,
            'address': self.address,
            'status': self.status,
            'total': self.total,
            'items': [item.to_dict() for item in self.items],
            'deliveryUpdates': json.loads(self.delivery_updates) if self.delivery_updates else [],
            'createdAt': self.created_at.isoformat()
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(50))
    image = db.Column(db.String(500))
    # NEW: Store the selected color for color selection feature
    selected_color = db.Column(db.String(100), default='')
    
    def to_dict(self):
        return {
            'productId': self.product_id,
            'name': self.product_name,
            'quantity': self.quantity,
            'price': self.price,
            'color': self.color,
            'image': self.image,
            # NEW: Include selected color in order item data
            'selected_color': self.selected_color
        }

class AdminAccessCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PromoCode(db.Model):
    __table_args__ = (
        # Performance indexes for promo codes
        db.Index('idx_promo_code', 'code'),
        db.Index('idx_promo_active', 'is_active'),
        db.Index('idx_promo_validity', 'valid_from', 'valid_until'),
        db.Index('idx_promo_usage', 'usage_limit', 'used_count'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0.0)
    max_discount = db.Column(db.Float, default=None)
    usage_limit = db.Column(db.Integer, default=None)  # None = unlimited
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_order_amount': self.min_order_amount,
            'max_discount': self.max_discount,
            'usage_limit': self.usage_limit,
            'used_count': self.used_count,
            'valid_from': self.valid_from.isoformat(),
            'valid_until': self.valid_until.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
    
    def is_valid(self, order_amount=0.0):
        """Check if promo code is valid for use"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if not (self.valid_from <= now <= self.valid_until):
            return False
        
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        
        if order_amount < self.min_order_amount:
            return False
        
        return True
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if self.discount_type == 'percentage':
            discount = order_amount * (self.discount_value / 100.0)
            if self.max_discount and discount > self.max_discount:
                return round(self.max_discount, 2)
            return round(discount, 2)
        else:  # fixed amount
            discount = min(self.discount_value, order_amount)
            return round(discount, 2)