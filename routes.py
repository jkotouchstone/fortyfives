from flask import Blueprint, jsonify, request
from game_logic import Game

# Define the Flask blueprint for game routes
fortyfives_bp = Blueprint('fortyfives', __name__)

# Initialize a new game instance
current_game = Game()

@fortyfives_bp.route("/new_game", methods=["POST"])
def new_game():
    """Starts a new game and deals hands to both players."""
    global current_game
    current_game = Game()  # Reset the game
    current_game.deal_hands()  # Deal cards to players and kitty
    print("DEBUG: New game started with hands dealt.")  # Log for debugging
    return jsonify({"message": "New game started successfully!"})

@fortyfives_bp.route("/show_state", methods=["GET"])
def show_state():
    """Returns the current game state to the frontend."""
    game_state = current_game.get_state()
    print("DEBUG: Game state returned:", game_state)  # Log for debugging
    return jsonify(game_state)

@fortyfives_bp.route("/play_card", methods=["POST"])
def play_card():
    """Handles playing a card during a trick."""
    data = request.json
    card_name = data.get("card_name")
    if not card_name:
        return jsonify({"message": "No card provided."}), 400

    result = current_game.play_card("player", card_name)
    return jsonify(result)

@fortyfives_bp.route("/bid", methods=["POST"])
def bid():
    """Handles the bidding process."""
    data = request.json
    bid_value = data.get("bid_value", 0)
    result = current_game.process_bid("player", bid_value)
    return jsonify({"message": result})

@fortyfives_bp.route("/computer_turn", methods=["POST"])
def computer_turn():
    """Handles the computer's turn during bidding or trick play."""
    if current_game.is_bidding_active():
        result = current_game.process_bid("computer", 20)  # Example computer bid
    elif current_game.is_card_play_allowed():
        result = current_game.play_card("computer", str(current_game.players["computer"]["hand"][0]))
    else:
        result = {"message": "No valid action for computer."}
    
    return jsonify(result)
