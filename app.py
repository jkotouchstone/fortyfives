from flask import Flask
from routes import fortyfives_bp  # Import the blueprint

app = Flask(__name__)
app.register_blueprint(fortyfives_bp)  # Register the blueprint with the app

if __name__ == '__main__':
    app.run(debug=True)
