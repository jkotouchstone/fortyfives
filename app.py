# app.py

from flask import Flask
from routes import fortyfives_bp

def create_app():
    app = Flask(__name__)
    # register blueprint
    app.register_blueprint(fortyfives_bp, url_prefix='/')
    return app

if __name__=="__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
