from flask import Blueprint, jsonify, request
from game_logic import Game

fortyfives_bp = Blueprint('fortyfives', __name__)
current_game = Game()

@fortyfives_bp.route("/show_state", methods=["GET"])
def show_state():
    game_state = current_game.get_state()
    return jsonify(game_state)

@fortyfives_bp.route("/new_game", methods=["POST"])
def new_game():
    global current_game
    current_game = Game()
    current_game.deal_hands()
    return jsonify({"message": "New game started!"})

@fortyfives_bp.route("/user_bid", methods=["POST"])
def user_bid():
    data = request.json
    bid_val = data.get("bid_val", 0)

    if not current_game.is_bidding_active():
        return jsonify({"message": "Bidding is not active."}), 400

    response_message = current_game.process_bid("player", bid_val)
    return jsonify({"message": response_message, "state": current_game.get_state()})

@fortyfives_bp.route("/play_card", methods=["POST"])
def play_card():
    data = request.json
    card_name = data.get("card_name")

    if not current_game.is_card_play_allowed():
        return jsonify({"message": "Not your turn to play."}), 400

    result = current_game.play_card("player", card_name)
    return jsonify(result)
