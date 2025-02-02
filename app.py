from flask import Flask
from routes import fortyfives_bp

# Initialize the Flask app
app = Flask(__name__)

# Register the blueprint with no URL prefix so routes match exactly
app.register_blueprint(fortyfives_bp)

@app.route("/")
def index():
    return "Welcome to the Forty-Fives Card Game API! Try accessing /show_state or /new_game"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
