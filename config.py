# MySQL Database Configuration
# UPDATE THESE VALUES to match your MySQL Workbench credentials

DB_CONFIG = {
    'host': 'localhost',       # Usually localhost
    'port': 3306,              # Default MySQL port
    'user': 'root',            # Your MySQL username
    'password': 'PKashyap@2007',  # ← REPLACE with your MySQL password
    'database': 'restaurant_management_system',
    'autocommit': False,
    'charset': 'utf8mb4'
}

# Flask server config
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG = True

# CORS allowed origins (frontend)
ALLOWED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:5500', 'http://localhost:5500', '*']
