from flask import Blueprint, jsonify, request
from models import PromoCode, db
from datetime import datetime

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/validate-promo', methods=['POST'])
def validate_promo_code():
    try:
        data = request.json
        promo_code = data.get('promoCode', '').strip().upper()
        order_amount = float(data.get('orderAmount', 0))
        
        if not promo_code:
            return jsonify({
                "valid": False,
                "message": "Promo code is required"
            }), 400
        
        # Find active promo code
        promo = PromoCode.query.filter_by(code=promo_code).first()
        
        if not promo:
            return jsonify({
                "valid": False,
                "message": "Invalid promo code"
            }), 400
        
        # Check if code is valid
        now = datetime.utcnow()
        if not promo.is_active:
            return jsonify({
                "valid": False,
                "message": "Promo code is not active"
            }), 400
        
        if now < promo.valid_from:
            return jsonify({
                "valid": False,
                "message": "Promo code is not yet active"
            }), 400
        
        if now > promo.valid_until:
            return jsonify({
                "valid": False,
                "message": "Promo code has expired"
            }), 400
        
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            return jsonify({
                "valid": False,
                "message": "Promo code usage limit reached"
            }), 400
        
        if order_amount < promo.min_order_amount:
            return jsonify({
                "valid": False,
                "message": f"Minimum order amount of {promo.min_order_amount} DZD required"
            }), 400
        
        # Calculate discount
        discount_amount = promo.calculate_discount(order_amount)
        final_amount = order_amount - discount_amount
        
        return jsonify({
            "valid": True,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "discount_type": promo.discount_type,
            "discount_value": promo.discount_value,
            "message": f"Promo code applied successfully! You saved {discount_amount} DZD!"
        })
        
    except ValueError:
        return jsonify({
            "valid": False,
            "message": "Invalid order amount"
        }), 400
    except Exception as e:
        return jsonify({
            "valid": False,
            "message": "Error validating promo code"
        }), 500

@cart_bp.route('/apply-promo', methods=['POST'])
def apply_promo_code():
    try:
        data = request.json
        promo_code = data.get('promoCode', '').strip().upper()
        order_amount = float(data.get('orderAmount', 0))
        
        if not promo_code:
            return jsonify({
                "success": False,
                "message": "Promo code is required"
            }), 400
        
        # Find active promo code
        promo = PromoCode.query.filter_by(code=promo_code).first()
        
        if not promo:
            return jsonify({
                "success": False,
                "message": "Invalid promo code"
            }), 400
        
        # Check if code is valid
        now = datetime.utcnow()
        if not promo.is_active:
            return jsonify({
                "success": False,
                "message": "Promo code is not active"
            }), 400
        
        if now < promo.valid_from:
            return jsonify({
                "success": False,
                "message": "Promo code is not yet active"
            }), 400
        
        if now > promo.valid_until:
            return jsonify({
                "success": False,
                "message": "Promo code has expired"
            }), 400
        
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            return jsonify({
                "success": False,
                "message": "Promo code usage limit reached"
            }), 400
        
        if order_amount < promo.min_order_amount:
            return jsonify({
                "success": False,
                "message": f"Minimum order amount of {promo.min_order_amount} DZD required"
            }), 400
        
        # Calculate discount
        discount_amount = promo.calculate_discount(order_amount)
        final_amount = order_amount - discount_amount
        
        # Increment usage count
        promo.used_count += 1
        db.session.commit()
        
        return jsonify({
            "success": True,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "discount_type": promo.discount_type,
            "discount_value": promo.discount_value,
            "message": f"Promo code applied successfully! You saved {discount_amount} DZD!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error applying promo code: {str(e)}"
        }), 500