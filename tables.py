from flask import Blueprint, jsonify, request
import mysql.connector
from config import DB_CONFIG

tables_bp = Blueprint('tables', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@tables_bp.route('/', methods=['GET'])
def get_tables():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM TABLE_INFO ORDER BY Table_ID")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@tables_bp.route('/', methods=['POST'])
def add_table():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO TABLE_INFO (Capacity, Location, Status) VALUES (%s,%s,%s)",
            (data.get('capacity', 4), data.get('location', 'Indoor'), data.get('status', 'Available'))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Table added'}), 201
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@tables_bp.route('/<int:tid>/status', methods=['PUT'])
def update_table_status(tid):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE TABLE_INFO SET Status=%s WHERE Table_ID=%s",
            (data['status'], tid)
        )
        conn.commit()
        return jsonify({'message': 'Status updated'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()
