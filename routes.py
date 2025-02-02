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
