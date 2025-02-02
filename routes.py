# routes.py

from flask import Blueprint, jsonify, request, render_template
from game_logic import Game, card_back_url, card_to_image_url

fortyfives_bp = Blueprint('fortyfives_bp', __name__, template_folder='templates')

current_game = None

@fortyfives_bp.route('/')
def index():
    global current_game
    # If no game or old game ended => new game
    if not current_game or current_game.game_over:
        current_game = Game()
        current_game.deal_hands()
    return render_template('index.html')

@fortyfives_bp.route('/show_state', methods=['GET'])
def show_state():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}),400

    user = current_game.players[0]
    comp = current_game.players[1]
    if user.score>=120 or comp.score>=120:
        current_game.game_over=True

    your_cards=[{"name":str(c),"img":card_to_image_url(str(c))} for c in user.hand]
    kitty_data=[{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]

    bidderName=None
    if current_game.bid_winner is not None:
        bidderName=current_game.players[current_game.bid_winner].name

    st={
      "computer_count": len(comp.hand),
      "your_cards": your_cards,
      "kitty": kitty_data,
      "kitty_revealed": current_game.kitty_revealed,
      "card_back": card_back_url(),
      "deck_count": len(current_game.deck.cards),
      "last_trick": current_game.last_played_cards,
      "round_score_your": user.tricks_won*5,
      "round_score_comp": comp.tricks_won*5,
      "total_your": user.score,
      "total_comp": comp.score,
      "bidder": bidderName,
      "bid_submitted": (current_game.bid_winner is not None),
      "bidding_done": current_game.bidding_done,
      "trump_suit": current_game.trump_suit,
      "trump_set": (current_game.trump_suit is not None),
      "leading_player": current_game.leading_player,
      "game_over": current_game.game_over
    }
    return jsonify(st)

@fortyfives_bp.route('/user_bid', methods=['POST'])
def user_bid():
    global current_game
    data=request.get_json() or {}
    val=data.get("bid_val",0)
    msg=current_game.user_bid(val)
    return jsonify({"message":msg})

@fortyfives_bp.route('/pick_trump', methods=['POST'])
def pick_trump():
    global current_game
    data=request.get_json() or {}
    suit=data.get("suit","Hearts")
    current_game.set_trump(suit)
    current_game.attach_kitty_user()  # user sees kitty if user is bidder
    return jsonify({"message":f"Trump suit set to {current_game.trump_suit}"})

@fortyfives_bp.route('/comp_discard', methods=['POST'])
def comp_discard():
    global current_game
    count=current_game.discard_comp()
    return jsonify({"message":f"Computer discarded {count} card(s). Drew {count}."})

@fortyfives_bp.route('/user_discard', methods=['POST'])
def user_discard():
    global current_game
    data=request.get_json() or {}
    discList=data.get("discards",[])
    c = current_game.discard_user(discList)
    return jsonify({"message":f"You discarded {c} card(s). Drew {c}."})

@fortyfives_bp.route('/both_discard_done', methods=['POST'])
def both_discard_done():
    global current_game
    current_game.both_discard_done_check()
    lead = current_game.leading_player
    leadName = current_game.players[lead].name if lead is not None else "None"
    return jsonify({"message":f"Discard done. {leadName} leads the first trick."})

# Additional routes for playing a trick (user lead, comp lead, etc.) can go here
