# routes.py
from flask import Blueprint, jsonify, request, render_template
from game_logic import Game, card_back_url, card_to_image_url

fortyfives_bp = Blueprint('fortyfives_bp', __name__, template_folder='templates')
current_game = None

@fortyfives_bp.route('/')
def index():
    global current_game
    if not current_game or current_game.game_over:
        current_game = Game()
        current_game.deal_hands()
    return render_template('index.html')

@fortyfives_bp.route('/show_state', methods=['GET'])
def show_state():
    global current_game
    if not current_game:
        return jsonify({"error": "No game in progress"}), 400
    user = current_game.players[0]
    comp = current_game.players[1]
    if user.score >= 120 or comp.score >= 120:
        current_game.game_over = True
    your_cards = [{"name": str(c), "img": card_to_image_url(str(c))} for c in user.hand]
    kitty = [{"name": str(c), "img": card_to_image_url(str(c))} for c in current_game.kitty]
    bidderName = None
    if current_game.bid_winner is not None:
        bidderName = current_game.players[current_game.bid_winner].name
    state = {
        "your_cards": your_cards,
        "computer_count": len(comp.hand),
        "kitty": kitty,
        "kitty_revealed": current_game.kitty_revealed,
        "card_back": card_back_url(),
        "deck_count": len(current_game.deck.cards),
        "last_trick": current_game.last_played_cards,
        "total_your": user.score,
        "total_comp": comp.score,
        "bidder": bidderName,
        "bidding_done": current_game.bidding_done,
        "trump_suit": current_game.trump_suit,
        "game_over": current_game.game_over,
        "leading_player": current_game.leading_player
    }
    return jsonify(state)

@fortyfives_bp.route('/user_bid', methods=['POST'])
def user_bid_route():
    global current_game
    data = request.get_json() or {}
    bid_val = data.get("bid_val", 0)
    msg = current_game.user_bid(bid_val)
    return jsonify({"message": msg})

@fortyfives_bp.route('/pick_trump', methods=['POST'])
def pick_trump():
    global current_game
    data = request.get_json() or {}
    suit = data.get("suit", "Hearts")
    current_game.set_trump(suit)
    current_game.attach_kitty_user()
    return jsonify({"message": f"Trump suit set to {current_game.trump_suit}"})

@fortyfives_bp.route('/comp_discard', methods=['POST'])
def comp_discard():
    global current_game
    count = current_game.discard_comp()
    return jsonify({"message": f"Computer discarded {count} card(s) and drew {count} new card(s)."} )

@fortyfives_bp.route('/user_discard', methods=['POST'])
def user_discard():
    global current_game
    data = request.get_json() or {}
    disc_list = data.get("discards", [])
    count = current_game.discard_user(disc_list)
    return jsonify({"message": f"You discarded {count} card(s) and drew {count} new card(s)."} )

@fortyfives_bp.route('/both_discard_done', methods=['POST'])
def both_discard_done():
    global current_game
    current_game.both_discard_done_check()
    lead = current_game.leading_player
    leadName = current_game.players[lead].name if lead is not None else "None"
    return jsonify({"message": f"Both discards done. {leadName} leads the first trick."})

# Routes for trick play:
@fortyfives_bp.route('/play_card_user_lead', methods=['POST'])
def play_card_user_lead():
    global current_game
    data = request.get_json() or {}
    card_name = data.get("card_name")
    msg = current_game.play_trick_user_lead(card_name)
    return jsonify({"message": msg})

@fortyfives_bp.route('/comp_lead_trick', methods=['POST'])
def comp_lead_trick():
    global current_game
    msg = current_game.comp_lead_trick()
    return jsonify({"message": msg})

@fortyfives_bp.route('/respond_comp_lead', methods=['POST'])
def respond_comp_lead():
    global current_game
    data = request.get_json() or {}
    card_name = data.get("card_name")
    msg = current_game.respond_to_comp_lead(card_name)
    return jsonify({"message": msg})
