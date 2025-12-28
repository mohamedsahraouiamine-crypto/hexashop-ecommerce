from flask import Blueprint, jsonify
from models import Order

tracking_bp = Blueprint('tracking', __name__)

@tracking_bp.route('/<order_id>')
def track_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    return jsonify(order.to_dict())