from flask import Blueprint, jsonify, request
import mysql.connector
from config import DB_CONFIG

orders_bp = Blueprint('orders', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@orders_bp.route('/', methods=['GET'])
def get_orders():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        status = request.args.get('status')
        if status:
            cursor.execute("""
                SELECT o.*, c.Name AS Customer_Name, s.Name AS Staff_Name,
                       t.Location AS Table_Location
                FROM ORDERS o
                JOIN CUSTOMER c   ON o.Customer_ID = c.Customer_ID
                JOIN STAFF s      ON o.Staff_ID    = s.Staff_ID
                JOIN TABLE_INFO t ON o.Table_ID    = t.Table_ID
                WHERE o.Order_Status = %s
                ORDER BY o.Order_Date DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT o.*, c.Name AS Customer_Name, s.Name AS Staff_Name,
                       t.Location AS Table_Location
                FROM ORDERS o
                JOIN CUSTOMER c   ON o.Customer_ID = c.Customer_ID
                JOIN STAFF s      ON o.Staff_ID    = s.Staff_ID
                JOIN TABLE_INFO t ON o.Table_ID    = t.Table_ID
                ORDER BY o.Order_Date DESC LIMIT 100
            """)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@orders_bp.route('/<int:oid>', methods=['GET'])
def get_order(oid):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT o.*, c.Name AS Customer_Name, c.Phone_No AS Customer_Phone,
                   s.Name AS Staff_Name, s.Role AS Staff_Role,
                   t.Location AS Table_Location, t.Capacity AS Table_Capacity
            FROM ORDERS o
            JOIN CUSTOMER c   ON o.Customer_ID = c.Customer_ID
            JOIN STAFF s      ON o.Staff_ID    = s.Staff_ID
            JOIN TABLE_INFO t ON o.Table_ID    = t.Table_ID
            WHERE o.Order_ID = %s
        """, (oid,))
        order = cursor.fetchone()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        cursor.execute("""
            SELECT oi.*, m.Item_Name, m.Category, m.Price AS Unit_Price
            FROM ORDER_ITEM oi
            JOIN MENU_ITEM m ON oi.Item_ID = m.Item_ID
            WHERE oi.Order_ID = %s
        """, (oid,))
        order['items'] = cursor.fetchall()

        cursor.execute("SELECT * FROM PAYMENT WHERE Order_ID=%s", (oid,))
        order['payment'] = cursor.fetchone()
        return jsonify(order)
    finally:
        cursor.close(); conn.close()

@orders_bp.route('/', methods=['POST'])
def create_order():
    data = request.json
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'No items provided'}), 400

        # Calculate total
        total = sum(i['price'] * i['quantity'] for i in items)

        cursor.execute("""
            INSERT INTO ORDERS (Customer_ID, Staff_ID, Table_ID, Total_Price, Payment_Mode, Notes)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (data['customer_id'], data['staff_id'], data['table_id'],
              total, data.get('payment_mode', 'Cash'), data.get('notes', '')))
        order_id = cursor.lastrowid

        for item in items:
            subtotal = item['price'] * item['quantity']
            cursor.execute("""
                INSERT INTO ORDER_ITEM (Order_ID, Item_ID, Quantity, Subtotal)
                VALUES (%s,%s,%s,%s)
            """, (order_id, item['item_id'], item['quantity'], subtotal))

        # Mark table as Occupied
        cursor.execute("UPDATE TABLE_INFO SET Status='Occupied' WHERE Table_ID=%s", (data['table_id'],))

        conn.commit()
        return jsonify({'order_id': order_id, 'total': total, 'message': 'Order created'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@orders_bp.route('/<int:oid>/status', methods=['PUT'])
def update_status(oid):
    data = request.json
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        new_status = data['status']
        cursor.execute("UPDATE ORDERS SET Order_Status=%s WHERE Order_ID=%s", (new_status, oid))

        # Free table when order completed/cancelled
        if new_status in ('Completed', 'Cancelled'):
            cursor.execute("SELECT Table_ID FROM ORDERS WHERE Order_ID=%s", (oid,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE TABLE_INFO SET Status='Available' WHERE Table_ID=%s", (row['Table_ID'],))

        conn.commit()
        return jsonify({'message': f'Order status updated to {new_status}'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@orders_bp.route('/<int:oid>', methods=['DELETE'])
def cancel_order(oid):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT Table_ID FROM ORDERS WHERE Order_ID=%s", (oid,))
        row = cursor.fetchone()
        cursor.execute("UPDATE ORDERS SET Order_Status='Cancelled' WHERE Order_ID=%s", (oid,))
        if row:
            cursor.execute("UPDATE TABLE_INFO SET Status='Available' WHERE Table_ID=%s", (row['Table_ID'],))
        conn.commit()
        return jsonify({'message': 'Order cancelled'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()
