from flask import Blueprint, jsonify, request
import mysql.connector
from config import DB_CONFIG

customers_bp = Blueprint('customers', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@customers_bp.route('/', methods=['GET'])
def get_customers():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM CUSTOMER ORDER BY Created_At DESC")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@customers_bp.route('/<int:cid>', methods=['GET'])
def get_customer(cid):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM CUSTOMER WHERE Customer_ID=%s", (cid,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        # Order history
        cursor.execute("""
            SELECT o.Order_ID, o.Order_Date, o.Total_Price, o.Order_Status
            FROM ORDERS o WHERE o.Customer_ID=%s ORDER BY o.Order_Date DESC LIMIT 10
        """, (cid,))
        row['orders'] = cursor.fetchall()
        return jsonify(row)
    finally:
        cursor.close(); conn.close()

@customers_bp.route('/', methods=['POST'])
def add_customer():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO CUSTOMER (Name, Phone_No, Email, Address) VALUES (%s,%s,%s,%s)",
            (data['name'], data['phone'], data.get('email'), data.get('address'))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Customer added'}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@customers_bp.route('/<int:cid>', methods=['PUT'])
def update_customer(cid):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE CUSTOMER SET Name=%s, Phone_No=%s, Email=%s, Address=%s WHERE Customer_ID=%s",
            (data['name'], data['phone'], data.get('email'), data.get('address'), cid)
        )
        conn.commit()
        return jsonify({'message': 'Updated'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@customers_bp.route('/<int:cid>', methods=['DELETE'])
def delete_customer(cid):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM CUSTOMER WHERE Customer_ID=%s", (cid,))
        conn.commit()
        return jsonify({'message': 'Deleted'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()
