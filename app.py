from flask import Flask
from routes import fortyfives_bp  # Now this import will succeed.

app = Flask(__name__)
app.register_blueprint(fortyfives_bp)  # Register the blueprint.

if __name__ == '__main__':
    app.run(debug=True)
