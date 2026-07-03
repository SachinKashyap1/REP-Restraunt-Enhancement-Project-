"""
ML Recommendation Engine for Restaurant Management System
Hybrid approach: Popularity + Category-based + Collaborative Filtering
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


class DishRecommender:
    """Hybrid dish recommendation system."""

    def __init__(self, db_connection_fn):
        """
        Args:
            db_connection_fn: callable that returns a mysql-connector connection
        """
        self.get_conn = db_connection_fn
        self.model = NearestNeighbors(n_neighbors=6, metric='cosine', algorithm='brute')
        self.scaler = StandardScaler()
        self.menu_df = None
        self.user_item_matrix = None
        self.is_trained = False

    # ------------------------------------------------------------------
    # Data Loading
    # ------------------------------------------------------------------
    def _load_menu(self):
        conn = self.get_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT Item_ID, Item_Name, Price, Category, Rating, Times_Ordered, Is_Available
            FROM MENU_ITEM WHERE Is_Available = 1
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        df = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=['Item_ID', 'Item_Name', 'Price', 'Category', 'Rating', 'Times_Ordered', 'Is_Available']
        )

        # MySQL returns Decimal / None — cast everything to safe Python types
        if not df.empty:
            df['Item_ID']      = pd.to_numeric(df['Item_ID'],      errors='coerce').fillna(0).astype(int)
            df['Price']        = pd.to_numeric(df['Price'],         errors='coerce').fillna(0.0).astype(float)
            df['Rating']       = pd.to_numeric(df['Rating'],        errors='coerce').fillna(0.0).astype(float)
            df['Times_Ordered']= pd.to_numeric(df['Times_Ordered'], errors='coerce').fillna(0).astype(int)

        self.menu_df = df
        return self.menu_df

    def _load_order_history(self):
        conn = self.get_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.Customer_ID, oi.Item_ID, SUM(oi.Quantity) AS qty
            FROM ORDER_ITEM oi
            JOIN ORDERS o ON oi.Order_ID = o.Order_ID
            WHERE o.Order_Status = 'Completed'
            GROUP BY o.Customer_ID, oi.Item_ID
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return pd.DataFrame(columns=['Customer_ID', 'Item_ID', 'qty'])

        df = pd.DataFrame(rows)
        # Cast Decimal → numeric to avoid pivot_table object-dtype issues
        df['Customer_ID'] = pd.to_numeric(df['Customer_ID'], errors='coerce')
        df['Item_ID']     = pd.to_numeric(df['Item_ID'],     errors='coerce')
        df['qty']         = pd.to_numeric(df['qty'],         errors='coerce').fillna(0)
        df = df.dropna(subset=['Customer_ID', 'Item_ID'])
        return df

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(self):
        """Train the collaborative filtering model on order history."""
        self._load_menu()
        history = self._load_order_history()

        if history.empty or len(history['Customer_ID'].unique()) < 3:
            self.is_trained = False
            return

        # Build user-item matrix — explicit float dtype prevents FutureWarning
        matrix = history.pivot_table(
            index='Customer_ID', columns='Item_ID', values='qty', fill_value=0
        ).astype(float)          # ← fixes FutureWarning: downcasting object dtype arrays

        self.user_item_matrix = matrix
        scaled = self.scaler.fit_transform(matrix.values)
        self.model.fit(scaled)
        self.is_trained = True

    # ------------------------------------------------------------------
    # Recommendation Methods
    # ------------------------------------------------------------------
    def recommend_popular(self, n=5, category=None):
        """Return top-N popular dishes, optionally filtered by category."""
        if self.menu_df is None:
            self._load_menu()
        df = self.menu_df.copy()
        if category:
            df = df[df['Category'] == category]
        if df.empty:
            return []

        max_ordered = df['Times_Ordered'].max()
        if max_ordered == 0:
            max_ordered = 1  # avoid division by zero

        df = df.copy()
        df['score'] = (df['Rating'] * 0.4) + (
            df['Times_Ordered'] / (max_ordered + 1) * 0.6
        )
        top = df.nlargest(n, 'score')
        return self._format(top, reason='🔥 Trending & Popular')

    def recommend_for_customer(self, customer_id, n=5):
        """
        Collaborative filtering: find similar customers and recommend
        items they ordered that this customer hasn't tried yet.
        Falls back to popularity if model not trained or customer unknown.
        """
        if not self.is_trained or self.user_item_matrix is None:
            return self.recommend_popular(n)

        if customer_id not in self.user_item_matrix.index:
            return self.recommend_popular(n)

        customer_vector = self.user_item_matrix.loc[customer_id].values.reshape(1, -1)
        scaled_vector = self.scaler.transform(customer_vector)
        distances, indices = self.model.kneighbors(scaled_vector)

        # Gather items from similar customers (excluding self)
        similar_customers = self.user_item_matrix.index[indices.flatten()[1:]]
        similar_orders = self.user_item_matrix.loc[similar_customers].sum(axis=0)

        # Remove items already ordered by this customer
        already_ordered = set(
            self.user_item_matrix.columns[self.user_item_matrix.loc[customer_id] > 0]
        )
        candidates = similar_orders.drop(
            labels=list(already_ordered & set(similar_orders.index)), errors='ignore'
        )
        top_item_ids = candidates.nlargest(n).index.tolist()

        if not top_item_ids:
            return self.recommend_popular(n)

        if self.menu_df is None:
            self._load_menu()
        result = self.menu_df[self.menu_df['Item_ID'].isin(top_item_ids)]
        return self._format(result, reason='⭐ Picked For You')

    def recommend_by_category(self, category, n=5):
        """Best-rated items in a specific category."""
        if self.menu_df is None:
            self._load_menu()
        df = self.menu_df[self.menu_df['Category'] == category].copy()
        if df.empty:
            return []
        top = df.nlargest(n, 'Rating')
        return self._format(top, reason=f'🍽️ Best {category}')

    def get_all_recommendations(self, customer_id=None, n=5):
        """
        Main entry point — returns a merged list from all strategies.
        """
        self.train()
        results = []

        if customer_id:
            personalized = self.recommend_for_customer(customer_id, n)
            results.extend(personalized)

        popular = self.recommend_popular(n)
        # Add only items not already in results
        existing_ids = {r['Item_ID'] for r in results}
        for dish in popular:
            if dish['Item_ID'] not in existing_ids:
                results.append(dish)
                existing_ids.add(dish['Item_ID'])
            if len(results) >= n * 2:
                break

        return results[:n * 2]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format(df, reason='Recommended'):
        dishes = []
        for _, row in df.iterrows():
            try:
                dishes.append({
                    'Item_ID':       int(row['Item_ID']),
                    'Item_Name':     str(row['Item_Name']),
                    'Price':         float(row['Price']),
                    'Category':      str(row['Category']),
                    'Rating':        float(row['Rating']),
                    'Times_Ordered': int(row['Times_Ordered']),
                    'Reason':        reason
                })
            except (ValueError, TypeError):
                # Skip any row that can't be cleanly serialised
                continue
        return dishes
