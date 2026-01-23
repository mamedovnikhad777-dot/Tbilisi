"""
SQL-запросы для генерации отчетов и аналитики
"""

# SQL-запросы для статистического отчета
statistical_queries = {
    "total_customers": "SELECT COUNT(*) as count FROM Customers",
    "total_restaurants": "SELECT COUNT(*) as count FROM Restaurants", 
    "total_couriers": "SELECT COUNT(*) as count FROM Couriers",
    "total_dishes": "SELECT COUNT(*) as count FROM Dishes",
    "total_orders": "SELECT COUNT(*) as count FROM Orders",
    "orders_by_status": """
        SELECT s.status_name, COUNT(o.order_id) as count 
        FROM Orders o 
        JOIN Statuses s ON o.status_id = s.status_id 
        GROUP BY s.status_name
    """,
    "orders_last_30_days": """
        SELECT DATE(order_time) as date, COUNT(*) as count 
        FROM Orders 
        WHERE order_time >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
        GROUP BY DATE(order_time) 
        ORDER BY date
    """,
    "popular_dishes": """
        SELECT d.name, COUNT(oi.order_id) as order_count 
        FROM OrderItems oi 
        JOIN Dishes d ON oi.dish_id = d.dish_id 
        GROUP BY d.dish_id, d.name 
        ORDER BY order_count DESC 
        LIMIT 5
    """,
    "restaurant_ratings": """
        SELECT name, rating 
        FROM Restaurants 
        WHERE rating IS NOT NULL 
        ORDER BY rating DESC 
        LIMIT 5
    """,
    "revenue_last_30_days": """
        SELECT DATE(order_time) as date, SUM(total_amount) as revenue
        FROM Orders
        WHERE order_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(order_time)
        ORDER BY date
    """,
    "average_order_value": """
        SELECT AVG(total_amount) as avg_order_value
        FROM Orders
        WHERE order_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """,
    "customer_retention": """
        SELECT 
            COUNT(DISTINCT customer_id) as total_customers,
            COUNT(DISTINCT CASE WHEN order_time >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN customer_id END) as active_customers
        FROM Orders
    """
}

# SQL-запросы для детального отчета
detailed_queries = {
    "customers_list": """
        SELECT 
            customer_id, 
            first_name, 
            last_name, 
            phone_number,
            created_at
        FROM Customers 
        ORDER BY last_name, first_name
    """,
    "orders_detailed": """
        SELECT 
            o.order_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            s.status_name,
            o.order_time,
            o.total_amount,
            COUNT(oi.order_id) as items_count,
            COALESCE(SUM(oi.quantity), 0) as total_quantity
        FROM Orders o
        LEFT JOIN Customers c ON o.customer_id = c.customer_id
        LEFT JOIN Statuses s ON o.status_id = s.status_id
        LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, c.first_name, c.last_name, s.status_name, o.order_time, o.total_amount
        ORDER BY o.order_time DESC
    """,
    "deliveries_info": """
        SELECT 
            d.delivery_id,
            o.order_id,
            CONCAT(cr.first_name, ' ', cr.last_name) as courier_name,
            cr.car_number,
            cr.phone_number as courier_phone,
            d.delivery_time,
            d.estimated_time,
            d.actual_time,
            d.status
        FROM Deliveries d
        LEFT JOIN Orders o ON d.order_id = o.order_id
        LEFT JOIN Couriers cr ON d.courier_id = cr.courier_id
        ORDER BY d.delivery_time DESC
    """,
    "order_items_detailed": """
        SELECT 
            oi.order_id,
            d.name as dish_name,
            r.name as restaurant_name,
            oi.quantity,
            d.cooking_time,
            oi.price_at_order,
            (oi.quantity * oi.price_at_order) as subtotal
        FROM OrderItems oi
        LEFT JOIN Dishes d ON oi.dish_id = d.dish_id
        LEFT JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        ORDER BY oi.order_id DESC
    """,
    "restaurants_detailed": """
        SELECT 
            r.restaurant_id,
            r.name,
            r.location,
            r.rating,
            r.phone_number,
            r.email,
            COUNT(DISTINCT d.dish_id) as dish_count,
            COUNT(DISTINCT oi.order_id) as order_count
        FROM Restaurants r
        LEFT JOIN Dishes d ON r.restaurant_id = d.restaurant_id
        LEFT JOIN OrderItems oi ON d.dish_id = oi.dish_id
        GROUP BY r.restaurant_id, r.name, r.location, r.rating, r.phone_number, r.email
        ORDER BY r.name
    """,
    "couriers_detailed": """
        SELECT 
            c.courier_id,
            CONCAT(c.first_name, ' ', c.last_name) as courier_name,
            c.phone_number,
            c.car_number,
            c.car_model,
            c.rating,
            c.is_active,
            COUNT(d.delivery_id) as delivery_count,
            AVG(TIMESTAMPDIFF(MINUTE, d.estimated_time, d.actual_time)) as avg_delay_minutes
        FROM Couriers c
        LEFT JOIN Deliveries d ON c.courier_id = d.courier_id
        GROUP BY c.courier_id, c.first_name, c.last_name, c.phone_number, 
                 c.car_number, c.car_model, c.rating, c.is_active
        ORDER BY c.last_name, c.first_name
    """
}

# Запросы для аналитики
analytical_queries = {
    "sales_trend": """
        SELECT 
            DATE_FORMAT(order_time, '%%Y-%%m') as month,
            COUNT(*) as order_count,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value
        FROM Orders
        WHERE order_time >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(order_time, '%%Y-%%m')
        ORDER BY month
    """,
    "customer_behavior": """
        SELECT 
            c.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            COUNT(o.order_id) as total_orders,
            SUM(o.total_amount) as total_spent,
            AVG(o.total_amount) as avg_order_value,
            MAX(o.order_time) as last_order_date,
            DATEDIFF(NOW(), MAX(o.order_time)) as days_since_last_order
        FROM Customers c
        LEFT JOIN Orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.first_name, c.last_name
        HAVING total_orders > 0
        ORDER BY total_spent DESC
    """,
    "dish_popularity": """
        SELECT 
            d.dish_id,
            d.name as dish_name,
            r.name as restaurant_name,
            COUNT(oi.order_id) as order_count,
            SUM(oi.quantity) as total_quantity,
            AVG(oi.quantity) as avg_quantity_per_order,
            SUM(oi.quantity * oi.price_at_order) as total_revenue
        FROM Dishes d
        LEFT JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        LEFT JOIN OrderItems oi ON d.dish_id = oi.dish_id
        GROUP BY d.dish_id, d.name, r.name
        ORDER BY order_count DESC
    """,
    "delivery_performance": """
        SELECT 
            cr.courier_id,
            CONCAT(cr.first_name, ' ', cr.last_name) as courier_name,
            COUNT(d.delivery_id) as total_deliveries,
            SUM(CASE WHEN d.status = 'доставлен' THEN 1 ELSE 0 END) as successful_deliveries,
            AVG(TIMESTAMPDIFF(MINUTE, d.estimated_time, d.actual_time)) as avg_delay_minutes,
            AVG(cr.rating) as avg_rating
        FROM Couriers cr
        LEFT JOIN Deliveries d ON cr.courier_id = d.courier_id
        GROUP BY cr.courier_id, cr.first_name, cr.last_name
        ORDER BY successful_deliveries DESC
    """,
    "time_analysis": """
        SELECT 
            HOUR(order_time) as hour_of_day,
            DAYNAME(order_time) as day_of_week,
            COUNT(*) as order_count,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value
        FROM Orders
        GROUP BY HOUR(order_time), DAYNAME(order_time)
        ORDER BY day_of_week, hour_of_day
    """
}

# Комплексные запросы для дашборда
dashboard_queries = {
    "today_stats": """
        SELECT 
            COUNT(*) as today_orders,
            SUM(total_amount) as today_revenue,
            AVG(total_amount) as today_avg_order
        FROM Orders
        WHERE DATE(order_time) = CURDATE()
    """,
    "weekly_comparison": """
        SELECT 
            'Эта неделя' as period,
            COUNT(*) as order_count,
            SUM(total_amount) as revenue
        FROM Orders
        WHERE YEARWEEK(order_time) = YEARWEEK(CURDATE())
        UNION ALL
        SELECT 
            'Прошлая неделя' as period,
            COUNT(*) as order_count,
            SUM(total_amount) as revenue
        FROM Orders
        WHERE YEARWEEK(order_time) = YEARWEEK(CURDATE()) - 1
    """,
    "top_customers": """
        SELECT 
            c.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            COUNT(o.order_id) as order_count,
            SUM(o.total_amount) as total_spent
        FROM Customers c
        JOIN Orders o ON c.customer_id = o.customer_id
        WHERE o.order_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY c.customer_id, c.first_name, c.last_name
        ORDER BY total_spent DESC
        LIMIT 10
    """,
    "recent_orders": """
        SELECT 
            o.order_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            s.status_name,
            o.order_time,
            o.total_amount
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
        JOIN Statuses s ON o.status_id = s.status_id
        ORDER BY o.order_time DESC
        LIMIT 10
    """,
    "system_health": """
        SELECT 
            'Всего заказов' as metric,
            COUNT(*) as value
        FROM Orders
        UNION ALL
        SELECT 
            'Активные курьеры' as metric,
            COUNT(*) as value
        FROM Couriers
        WHERE is_active = 1
        UNION ALL
        SELECT 
            'Доступные блюда' as metric,
            COUNT(*) as value
        FROM Dishes
        WHERE is_available = 1
        UNION ALL
        SELECT 
            'Средний рейтинг ресторанов' as metric,
            ROUND(AVG(rating), 2) as value
        FROM Restaurants
        WHERE rating IS NOT NULL
    """
}
