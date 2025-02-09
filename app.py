from flask import Flask, request, jsonify, send_from_directory
from game_logic import Game

app = Flask(__name__, static_folder="static")
current_game = None

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/start_game", methods=["POST"])
def start_game():
    global current_game
    try:
        data = request.get_json()
        mode = data.get("mode", "2p")
        instructional = data.get("instructional", False)
        current_game = Game(mode=mode, instructional=instructional)
        return jsonify(current_game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/bid", methods=["POST"])
def bid():
    global current_game
    try:
        if not current_game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        player_bid = data.get("bid", 0)
        current_game.process_bid(player_bid)
        return jsonify(current_game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/select_trump", methods=["POST"])
def select_trump():
    global current_game
    try:
        if not current_game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        trump = data.get("trump")
        current_game.select_trump(trump)
        return jsonify(current_game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/confirm_kitty", methods=["POST"])
def confirm_kitty():
    global current_game
    try:
        if not current_game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        keptIndices = data.get("keptIndices", [])
        current_game.confirm_kitty(keptIndices)
        return jsonify(current_game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/confirm_draw", methods=["POST"])
def confirm_draw():
    global current_game
    try:
        if not current_game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        keptIndices = data.get("keptIndices", None)
        current_game.confirm_draw(keptIndices)
        return jsonify(current_game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/play_trick", methods=["POST"])
def play_trick():
    global current_game
    try:
        if not current_game:
            return jsonify({"error": "No game started."}), 500
        data = request.get_json()
        cardIndex = data.get("cardIndex")
        if cardIndex is None:
            return jsonify({"error": "cardIndex required."}), 500
        current_game.play_card("player", cardIndex)
        return jsonify(current_game.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset_game", methods=["POST"])
def reset_game():
    global current_game
    try:
        current_game = None
        return jsonify({"message": "Game reset. Please start a new game."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
