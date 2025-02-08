from flask import Flask, request, jsonify
from game_logic import Game

app = Flask(__name__)
current_game = None  # Global game instance

@app.route("/start_game", methods=["POST"])
def start_game():
    global current_game
    data = request.get_json()
    mode = data.get("mode", "2p")
    instructional = data.get("instructional", False)
    current_game = Game(mode=mode, instructional=instructional)
    return jsonify(current_game.to_dict())

@app.route("/bid", methods=["POST"])
def bid():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game started."})
    data = request.get_json()
    player_bid = data.get("bid", 0)
    current_game.process_bid(player_bid)
    return jsonify(current_game.to_dict())

@app.route("/select_trump", methods=["POST"])
def select_trump():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game started."})
    data = request.get_json()
    trump = data.get("trump")
    current_game.select_trump(trump)
    return jsonify(current_game.to_dict())

@app.route("/confirm_kitty", methods=["POST"])
def confirm_kitty():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game started."})
    data = request.get_json()
    keptIndices = data.get("keptIndices", [])
    current_game.confirm_kitty(keptIndices)
    return jsonify(current_game.to_dict())

@app.route("/confirm_draw", methods=["POST"])
def confirm_draw():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game started."})
    current_game.confirm_draw()
    return jsonify(current_game.to_dict())

@app.route("/play_trick", methods=["POST"])
def play_trick():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game started."})
    data = request.get_json()
    cardIndex = data.get("cardIndex")
    if cardIndex is None:
        return jsonify({"error": "cardIndex required."})
    current_game.play_trick(cardIndex)
    return jsonify(current_game.to_dict())

@app.route("/reset_game", methods=["POST"])
def reset_game():
    global current_game
    current_game = None
    return jsonify({"message": "Game reset. Please start a new game."})

@app.route("/state", methods=["GET"])
def state():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game started."})
    return jsonify(current_game.to_dict())

if __name__ == "__main__":
    app.run(debug=True)
