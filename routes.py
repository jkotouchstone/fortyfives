from flask import Blueprint, jsonify, request
from game_logic import Game

# Define the blueprint for routes
fortyfives_bp = Blueprint('fortyfives', __name__)

# Initialize the game instance
current_game = Game()

@fortyfives_bp.route("/new_game", methods=["POST"])
def new_game():
    """Start a new game and deal hands to both players."""
    global current_game
    current_game = Game()
    current_game.deal_hands()
    return jsonify({"message": "New game started successfully!"})

@fortyfives_bp.route("/show_state", methods=["GET"])
def show_state():
    """Return the current game state."""
    game_state = current_game.get_state()
    return jsonify(game_state)

@fortyfives_bp.route("/bid", methods=["POST"])
def bid():
    """Handle the bidding process."""
    data = request.json
    bid_value = data.get("bid_value", 0)
    result = current_game.process_bid("player", bid_value)
    return jsonify({"message": result})

@fortyfives_bp.route("/trump_selection", methods=["POST"])
def trump_selection():
    """Handle trump selection after the bidding phase."""
    data = request.json
    trump_suit = data.get("trump_suit")
    current_game.trump_suit = trump_suit
    current_game.start_discard_phase()
    return jsonify({"message": f"Trump suit selected: {trump_suit}"})

@fortyfives_bp.route("/discard_cards", methods=["POST"])
def discard_cards():
    """Handle the discard and draw phase."""
    data = request.json
    cards_to_discard = data.get("cards", [])
    result = current_game.discard_cards("player", cards_to_discard)
    return jsonify(result)

@fortyfives_bp.route("/play_card", methods=["POST"])
def play_card():
    """Play a card during the trick phase."""
    data = request.json
    card_name = data.get("card_name")
    if not card_name:
        return jsonify({"message": "No card provided."}), 400

    result = current_game.play_card("player", card_name)
    return jsonify(result)
