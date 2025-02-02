from flask import Flask
from routes import fortyfives_bp

app = Flask(__name__)
app.register_blueprint(fortyfives_bp, url_prefix="/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
