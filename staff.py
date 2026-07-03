from flask import Blueprint, jsonify, request
import mysql.connector
from config import DB_CONFIG

staff_bp = Blueprint('staff', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@staff_bp.route('/', methods=['GET'])
def get_staff():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM STAFF ORDER BY Name")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@staff_bp.route('/', methods=['POST'])
def add_staff():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO STAFF (Name, Role, Phone_No, Salary) VALUES (%s,%s,%s,%s)",
            (data['name'], data['role'], data.get('phone'), data.get('salary', 0))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Staff added'}), 201
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@staff_bp.route('/<int:sid>', methods=['PUT'])
def update_staff(sid):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE STAFF SET Name=%s, Role=%s, Phone_No=%s, Salary=%s WHERE Staff_ID=%s",
            (data['name'], data['role'], data.get('phone'), data.get('salary', 0), sid)
        )
        conn.commit()
        return jsonify({'message': 'Updated'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@staff_bp.route('/<int:sid>', methods=['DELETE'])
def delete_staff(sid):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM STAFF WHERE Staff_ID=%s", (sid,))
        conn.commit()
        return jsonify({'message': 'Deleted'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()
