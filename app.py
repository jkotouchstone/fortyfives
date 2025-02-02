from flask import Flask, render_template
from routes import fortyfives_bp

# Initialize the Flask app
app = Flask(__name__)

# Register the game routes
app.register_blueprint(fortyfives_bp)

# Serve the main game page (index.html)
@app.route("/")
def index():
    return render_template("index.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
