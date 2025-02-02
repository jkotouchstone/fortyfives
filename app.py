# app.py
from flask import Flask
from routes import fortyfives_bp

def create_app():
    app = Flask(__name__)
    # Register the blueprint from routes.py
    app.register_blueprint(fortyfives_bp, url_prefix='/')
    return app

if __name__ == "__main__":
    app = create_app()
    # Render typically runs python app.py by default. This is all you need.
    app.run(host="0.0.0.0", port=5000, debug=False)
