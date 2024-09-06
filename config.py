import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '4fb6763d012413e746b7a65d4fb06c891eff2d29c804a939abee26e104859f27'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or '4fb6763d012413e746b7a65d4fb06c891eff2d29c804a939abee26e104859f27'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'postgresql://postgres:admin@localhost/secure_api'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    HOST = '127.0.0.1'
    PORT = 5000
    JWT_TOKEN_LOCATION = ['cookies']  # Specify that tokens are located in cookies
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'  # Set the cookie name
    JWT_ACCESS_COOKIE_PATH = '/'  # Path to send the access cookie
    JWT_ACCESS_COOKIE_SECURE = False  # Set to True if using HTTPS
    JWT_ACCESS_COOKIE_SAMESITE = 'Lax'  # Adjust based on your requirements
    JWT_COOKIE_CSRF_PROTECT = False

    WTF_CSRF_ENABLED = False
    WTF_CSRF_SECRET_KEY = 'IjExZTlmNWU3MTUzYzc4ZTZlODQwZDY2ZGNkYWQzNzVhMWVhNjU5NDUi.ZtS-Jw.iok0Uagw5DRjZpxDntIH_kVg0Rw'

    TESTING = True