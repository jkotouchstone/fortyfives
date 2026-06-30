import os
import uuid
from flask import Flask, request, jsonify, send_from_directory, session
from game_logic import Game
from store import load_game, save_game, delete_game

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

def get_session_id():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    session.permanent = True
    return session["sid"]

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/start_game", methods=["POST"])
def start_game():
    try:
        sid = get_session_id()
        data = request.get_json()
        mode = data.get("mode", "2p")
        instructional = data.get("instructional", False)
        game = Game(mode=mode, instructional=instructional)
        save_game(sid, game)
        return jsonify(game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/bid", methods=["POST"])
def bid():
    try:
        sid = get_session_id()
        game = load_game(sid)
        if not game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        player_bid = data.get("bid", 0)
        game.process_bid(player_bid)
        save_game(sid, game)
        return jsonify(game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/select_trump", methods=["POST"])
def select_trump():
    try:
        sid = get_session_id()
        game = load_game(sid)
        if not game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        trump = data.get("trump")
        game.select_trump(trump)
        save_game(sid, game)
        return jsonify(game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/confirm_kitty", methods=["POST"])
def confirm_kitty():
    try:
        sid = get_session_id()
        game = load_game(sid)
        if not game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        keptIndices = data.get("keptIndices", [])
        game.confirm_kitty(keptIndices)
        save_game(sid, game)
        return jsonify(game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/confirm_draw", methods=["POST"])
def confirm_draw():
    try:
        sid = get_session_id()
        game = load_game(sid)
        if not game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        keptIndices = data.get("keptIndices", None)
        game.confirm_draw(keptIndices)
        save_game(sid, game)
        return jsonify(game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/play_trick", methods=["POST"])
def play_trick():
    try:
        sid = get_session_id()
        game = load_game(sid)
        if not game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        cardText = data.get("cardText")
        if cardText is None:
            return jsonify({"error": "cardText required."}), 500
        state = game.play_card("player", cardText)
        save_game(sid, game)
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear_trick", methods=["POST"])
def clear_trick():
    try:
        sid = get_session_id()
        game = load_game(sid)
        if not game:
            return jsonify({"error": "No game started."}), 500
        state = game.clear_trick()
        save_game(sid, game)
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset_game", methods=["POST"])
def reset_game():
    try:
        sid = get_session_id()
        delete_game(sid)
        return jsonify({"message": "Game reset. Please start a new game."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
