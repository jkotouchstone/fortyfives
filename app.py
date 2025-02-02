from flask import Flask, render_template
from routes import fortyfives_bp

app = Flask(__name__)

# Register the blueprint
app.register_blueprint(fortyfives_bp, url_prefix="/")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
