from flask import Blueprint, jsonify, request
from models import Order, OrderItem, Product, PromoCode, db
from datetime import datetime
import json
import random
import string
import time
from sqlalchemy.exc import OperationalError
from routes.products import invalidate_product_cache

orders_bp = Blueprint('orders', __name__)

def generate_order_id():
    return 'ORD-' + ''.join(random.choices(string.digits, k=6))

def validate_phone_number(phone):
    import re
    pattern = r'^(\+213|0)[5-7][0-9]{8}$'
    return re.match(pattern, phone.replace(' ', '')) is not None

@orders_bp.route('/', methods=['POST'])
def create_order():
    max_retries = 3
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            data = request.json
            required_fields = ['phoneNumber', 'customerName', 'wilaya', 'address', 'items']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400

            phone_number = data['phoneNumber'].strip()
            customer_name = data['customerName'].strip()
            wilaya = data['wilaya'].strip()
            address = data['address'].strip()

            if not validate_phone_number(phone_number):
                return jsonify({"error": "Invalid phone format"}), 400

            # 1. Prepare data and verify stock
            total = 0
            temp_items = []
            
            for item_data in data['items']:
                product = Product.query.get(item_data['productId'])
                if not product:
                    return jsonify({"error": f"Product not found: {item_data['productId']}"}), 400
                
                quantity = int(item_data.get('quantity', 0))
                selected_color = item_data.get('selected_color', '')
                
                if not selected_color:
                    return jsonify({"error": f"Color selection required for {product.title}"}), 400
                
                # Check Stock
                current_stock = product.get_color_stock(selected_color)
                if current_stock < quantity:
                    return jsonify({"error": f"Out of stock for {product.title} ({selected_color})"}), 400
                
                # Subtract Stock Locally
                product.update_color_stock(selected_color, current_stock - quantity)
                
                item_price = product.discount_price if product.has_active_discount() else product.price
                total += item_price * quantity
                temp_items.append({
                    'product_id': product.id,
                    'name': product.title,
                    'quantity': quantity,
                    'price': item_price,
                    'color': item_data.get('color', ''),
                    'image': item_data.get('image', ''),
                    'selected_color': selected_color
                })

            # 2. Promo Code Logic
            promo_code = data.get('promoCode')
            if promo_code:
                promo = PromoCode.query.filter_by(code=promo_code.upper()).first()
                if promo and promo.is_active and total >= promo.min_order_amount:
                    total -= promo.calculate_discount(total)
                    promo.used_count += 1

            # 3. Create the actual Order records
            order = Order(
                id=generate_order_id(),
                phone_number=phone_number,
                customer_name=customer_name,
                wilaya=wilaya,
                address=address,
                total=total,
                status='pending',
                delivery_updates=json.dumps([{
                    'date': datetime.utcnow().isoformat(),
                    'status': 'ordered',
                    'message': 'Order received'
                }])
            )
            db.session.add(order)

            for ti in temp_items:
                item = OrderItem(
                    order_id=order.id,
                    product_id=ti['product_id'],
                    product_name=ti['name'],
                    quantity=ti['quantity'],
                    price=ti['price'],
                    color=ti['color'],
                    image=ti['image'],
                    selected_color=ti['selected_color']
                )
                db.session.add(item)

            # 4. FINAL COMMIT (Saves stock and order together)
            db.session.commit()
            
            invalidate_product_cache()
            return jsonify({
                "message": "Order created successfully",
                "orderId": order.id,
                "order": order.to_dict()
            }), 201

        except OperationalError as e:
            db.session.rollback()
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return jsonify({"error": "Database busy"}), 503
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Failed to process order"}), 503

@orders_bp.route('/phone/<phone_number>')
def get_orders_by_phone(phone_number):
    if not validate_phone_number(phone_number):
        return jsonify({"error": "Invalid phone"}), 400
    orders = Order.query.filter_by(phone_number=phone_number).order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])