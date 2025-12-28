from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db():
    # Create all tables
    db.create_all()
    
    from models import Product, Order, PromoCode, OrderItem, AdminAccessCode, AdminUser  # noqa: F401

    # Comprehensive index creation with error handling
    index_statements = [
        # Product indexes
        'CREATE INDEX IF NOT EXISTS idx_product_brand ON product (brand)',
        'CREATE INDEX IF NOT EXISTS idx_product_model ON product (model)',
        'CREATE INDEX IF NOT EXISTS idx_product_type ON product (type)',
        'CREATE INDEX IF NOT EXISTS idx_product_featured ON product (is_featured)',
        'CREATE INDEX IF NOT EXISTS idx_product_created ON product (created_at)',
        'CREATE INDEX IF NOT EXISTS idx_product_discount ON product (discount_active, discount_end)',
        'CREATE INDEX IF NOT EXISTS idx_product_model_featured ON product (model, is_featured)',
        'CREATE INDEX IF NOT EXISTS idx_product_brand_model ON product (brand, model)',
        
        # Order indexes
        'CREATE INDEX IF NOT EXISTS idx_order_status ON "order" (status)',
        'CREATE INDEX IF NOT EXISTS idx_order_phone ON "order" (phone_number)',
        'CREATE INDEX IF NOT EXISTS idx_order_created ON "order" (created_at)',
        'CREATE INDEX IF NOT EXISTS idx_order_status_created ON "order" (status, created_at)',
        'CREATE INDEX IF NOT EXISTS idx_order_phone_created ON "order" (phone_number, created_at)',
        
        # OrderItem indexes
        'CREATE INDEX IF NOT EXISTS idx_orderitem_order ON order_item (order_id)',
        'CREATE INDEX IF NOT EXISTS idx_orderitem_product ON order_item (product_id)',
        
        # PromoCode indexes
        'CREATE INDEX IF NOT EXISTS idx_promo_code ON promo_code (code)',
        'CREATE INDEX IF NOT EXISTS idx_promo_active ON promo_code (is_active)',
        'CREATE INDEX IF NOT EXISTS idx_promo_valid ON promo_code (valid_from, valid_until)',
        'CREATE INDEX IF NOT EXISTS idx_promo_usage ON promo_code (usage_limit, used_count)',
        
        # Admin indexes
        'CREATE INDEX IF NOT EXISTS idx_admin_user ON admin_user (username)',
        'CREATE INDEX IF NOT EXISTS idx_admin_code ON admin_access_code (code)',
    ]

    try:
        with db.engine.connect() as connection:
            for statement in index_statements:
                try:
                    connection.execute(text(statement))
                except Exception as index_error:
                    print(f"⚠️ Could not create index {statement}: {index_error}")
        
        print("✅ Database tables and indexes optimized")
        
        # Verify indexes exist
        with db.engine.connect() as connection:
            result = connection.execute(text("""
                SELECT schemaname, tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                ORDER BY tablename, indexname
            """))
            indexes = result.fetchall()
            print(f"📊 Total database indexes: {len(indexes)}")
            
    except Exception as e:
        print(f"⚠️ Database optimization note: {e}")