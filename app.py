# app.py
from flask import Flask
from routes import fortyfives_bp

def create_app():
    app = Flask(__name__)
    # Register the blueprint from routes.py
    app.register_blueprint(fortyfives_bp, url_prefix='/')
    return app

if __name__ == "__main__":
    # This is the file Render will run by default (python app.py)
    app = create_app()
    # If debugging locally, you can enable debug=True
    app.run(host="0.0.0.0", port=5000, debug=False)
