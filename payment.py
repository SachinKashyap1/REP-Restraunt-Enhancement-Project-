from flask import Blueprint, jsonify, request
import mysql.connector
import uuid
from config import DB_CONFIG

payment_bp = Blueprint('payment', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@payment_bp.route('/', methods=['GET'])
def get_payments():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, c.Name AS Customer_Name, o.Total_Price AS Order_Total
            FROM PAYMENT p
            JOIN ORDERS o   ON p.Order_ID   = o.Order_ID
            JOIN CUSTOMER c ON o.Customer_ID = c.Customer_ID
            ORDER BY p.Payment_Date DESC LIMIT 100
        """)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@payment_bp.route('/<int:pid>', methods=['GET'])
def get_payment(pid):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, c.Name AS Customer_Name, o.Order_Date, o.Total_Price
            FROM PAYMENT p
            JOIN ORDERS o   ON p.Order_ID   = o.Order_ID
            JOIN CUSTOMER c ON o.Customer_ID = c.Customer_ID
            WHERE p.Payment_ID = %s
        """, (pid,))
        row = cursor.fetchone()
        return jsonify(row) if row else (jsonify({'error': 'Not found'}), 404)
    finally:
        cursor.close(); conn.close()

@payment_bp.route('/order/<int:oid>', methods=['GET'])
def get_payment_by_order(oid):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM PAYMENT WHERE Order_ID=%s", (oid,))
        row = cursor.fetchone()
        return jsonify(row) if row else (jsonify({'exists': False}), 200)
    finally:
        cursor.close(); conn.close()

@payment_bp.route('/', methods=['POST'])
def process_payment():
    data = request.json
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        order_id = data['order_id']

        # Verify order exists
        cursor.execute("SELECT * FROM ORDERS WHERE Order_ID=%s", (order_id,))
        order = cursor.fetchone()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Generate transaction ID
        txn_id = data.get('transaction_id') or f"TXN{uuid.uuid4().hex[:10].upper()}"

        cursor.execute("""
            INSERT INTO PAYMENT (Order_ID, Amount, Payment_Method, Transaction_ID, Status)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                Amount=%s, Payment_Method=%s, Transaction_ID=%s, Status=%s, Payment_Date=NOW()
        """, (
            order_id, data['amount'], data['method'], txn_id, data.get('status', 'Success'),
            data['amount'], data['method'], txn_id, data.get('status', 'Success')
        ))

        # Mark order as completed if payment successful
        if data.get('status', 'Success') == 'Success':
            cursor.execute(
                "UPDATE ORDERS SET Order_Status='Completed', Payment_Mode=%s WHERE Order_ID=%s",
                (data['method'], order_id)
            )
            cursor.execute("""
                SELECT Table_ID FROM ORDERS WHERE Order_ID=%s
            """, (order_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE TABLE_INFO SET Status='Available' WHERE Table_ID=%s", (row['Table_ID'],))

        conn.commit()
        return jsonify({'transaction_id': txn_id, 'message': 'Payment processed'}), 201
    except mysql.connector.IntegrityError as e:
        conn.rollback()
        return jsonify({'error': 'Payment already exists for this order. Use update endpoint.'}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@payment_bp.route('/<int:pid>/refund', methods=['PUT'])
def refund_payment(pid):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE PAYMENT SET Status='Refunded' WHERE Payment_ID=%s", (pid,))
        conn.commit()
        return jsonify({'message': 'Payment refunded'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@payment_bp.route('/summary', methods=['GET'])
def payment_summary():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                COUNT(*) AS total_payments,
                SUM(CASE WHEN Status='Success'  THEN Amount ELSE 0 END) AS total_collected,
                SUM(CASE WHEN Status='Refunded' THEN Amount ELSE 0 END) AS total_refunded,
                SUM(CASE WHEN Status='Pending'  THEN Amount ELSE 0 END) AS total_pending,
                COUNT(CASE WHEN Payment_Method='Cash'   THEN 1 END) AS cash_count,
                COUNT(CASE WHEN Payment_Method='Card'   THEN 1 END) AS card_count,
                COUNT(CASE WHEN Payment_Method='UPI'    THEN 1 END) AS upi_count,
                COUNT(CASE WHEN Payment_Method='Online' THEN 1 END) AS online_count
            FROM PAYMENT
            WHERE DATE(Payment_Date) = CURDATE()
        """)
        return jsonify(cursor.fetchone())
    finally:
        cursor.close(); conn.close()
