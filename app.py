from flask import Flask, render_template
from routes import fortyfives_bp

# Initialize the Flask app
app = Flask(__name__)

# Register the game routes blueprint
app.register_blueprint(fortyfives_bp)

# Serve the main HTML page
@app.route("/")
def index():
    return render_template("index.html")

# Start the app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
