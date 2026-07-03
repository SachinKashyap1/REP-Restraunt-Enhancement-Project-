from flask import Blueprint, jsonify, request, current_app
import mysql.connector
from config import DB_CONFIG
from ml.recommender import DishRecommender

recommendation_bp = Blueprint('recommendation', __name__)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

_recommender = DishRecommender(get_db)

@recommendation_bp.route('/', methods=['GET'])
def get_recommendations():
    """
    GET /api/recommend/?customer_id=1&category=Main Course&n=5
    Returns top dish recommendations.
    """
    customer_id = request.args.get('customer_id', type=int)
    category    = request.args.get('category')
    n           = request.args.get('n', 5, type=int)

    try:
        _recommender.train()

        if category:
            results = _recommender.recommend_by_category(category, n)
        elif customer_id:
            results = _recommender.get_all_recommendations(customer_id, n)
        else:
            results = _recommender.recommend_popular(n)

        return jsonify({'recommendations': results, 'count': len(results)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recommendation_bp.route('/popular', methods=['GET'])
def popular():
    n = request.args.get('n', 5, type=int)
    try:
        results = _recommender.recommend_popular(n)
        return jsonify({'recommendations': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recommendation_bp.route('/best-dishes', methods=['GET'])
def best_dishes():
    """Top dish per category — for the homepage showcase."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m1.Item_ID, m1.Item_Name, m1.Category, m1.Price, m1.Rating, m1.Times_Ordered, m1.Description
            FROM MENU_ITEM m1
            INNER JOIN (
                SELECT Category, MAX(Rating) AS max_rating
                FROM MENU_ITEM WHERE Is_Available=1
                GROUP BY Category
            ) best ON m1.Category = best.Category AND m1.Rating = best.max_rating
            WHERE m1.Is_Available=1
            ORDER BY m1.Category
        """)
        rows = cursor.fetchall()
        return jsonify({'best_dishes': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()
