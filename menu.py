from flask import Blueprint, jsonify, request
import mysql.connector
from config import DB_CONFIG

menu_bp = Blueprint('menu', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@menu_bp.route('/', methods=['GET'])
def get_menu():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        category = request.args.get('category')
        if category:
            cursor.execute(
                "SELECT * FROM MENU_ITEM WHERE Category=%s AND Is_Available=1 ORDER BY Item_Name",
                (category,)
            )
        else:
            cursor.execute("SELECT * FROM MENU_ITEM WHERE Is_Available=1 ORDER BY Category, Item_Name")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@menu_bp.route('/all', methods=['GET'])
def get_all_menu():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM MENU_ITEM ORDER BY Category, Item_Name")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@menu_bp.route('/<int:iid>', methods=['GET'])
def get_item(iid):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM MENU_ITEM WHERE Item_ID=%s", (iid,))
        row = cursor.fetchone()
        return jsonify(row) if row else (jsonify({'error': 'Not found'}), 404)
    finally:
        cursor.close(); conn.close()

@menu_bp.route('/', methods=['POST'])
def add_item():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO MENU_ITEM (Item_Name, Price, Category, Description, Rating, Is_Available)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (data['name'], data['price'], data['category'],
             data.get('description', ''), data.get('rating', 0), data.get('available', 1))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Item added'}), 201
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@menu_bp.route('/<int:iid>', methods=['PUT'])
def update_item(iid):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE MENU_ITEM SET Item_Name=%s, Price=%s, Category=%s,
               Description=%s, Rating=%s, Is_Available=%s WHERE Item_ID=%s""",
            (data['name'], data['price'], data['category'],
             data.get('description', ''), data.get('rating', 0),
             data.get('available', 1), iid)
        )
        conn.commit()
        return jsonify({'message': 'Updated'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@menu_bp.route('/<int:iid>', methods=['DELETE'])
def delete_item(iid):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE MENU_ITEM SET Is_Available=0 WHERE Item_ID=%s", (iid,))
        conn.commit()
        return jsonify({'message': 'Item removed from menu'})
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()
