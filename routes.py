# routes.py

from flask import Blueprint, jsonify, request, render_template
from game_logic import Game, card_back_url, card_to_image_url, ...

# A blueprint for routes, or you could keep it simpler in a single app object
fortyfives_bp = Blueprint('fortyfives_bp', __name__, template_folder='templates')

current_game = None

@fortyfives_bp.route('/')
def index():
    global current_game
    if not current_game or current_game.game_over:
        current_game = Game()
        current_game.deal_hands()
    # You can either do: return render_template('index.html')
    # or build an inline HTML string
    return render_template('index.html')

@fortyfives_bp.route('/reset_game', methods=["POST"])
def reset_game():
    global current_game
    current_game = Game()
    current_game.deal_hands()
    return jsonify({"message":"New game started"})

@fortyfives_bp.route('/show_state', methods=["GET"])
def show_state():
    global current_game
    if not current_game:
        return jsonify({"error":"No game"}),400
    user = current_game.players[0]
    comp = current_game.players[1]
    if user.score >=120 or comp.score >=120:
        current_game.game_over=True

    # Build JSON
    your_cards = [{"name":str(c),"img": card_to_image_url(str(c))} for c in user.hand]
    kitty_info = [{"name":str(c),"img": card_to_image_url(str(c))} for c in current_game.kitty]
    # etc.

    return jsonify({
        "computer_count": len(comp.hand),
        "your_cards": your_cards,
        # ...
    })

@fortyfives_bp.route('/user_bid', methods=["POST"])
def user_bid():
    global current_game
    data = request.json or {}
    val = data.get("bid_val",0)
    msg = current_game.user_bid(val)
    return jsonify({"message":msg})

# and so forth for /pick_trump, /comp_discard, /user_discard, 
# /play_card_user_lead, /comp_lead_trick, etc.
