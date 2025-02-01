import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

game_mode = None
current_game = None  # Will point to a Game instance

#################################
#         GAME CLASSES          #
#################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self, num_decks=1):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = []
        for _ in range(num_decks):
            for s in suits:
                for r in ranks:
                    self.cards.append(Card(s, r))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0

    def add_to_hand(self, cards):
        self.hand.extend(cards)

class Game:
    def __init__(self, mode):
        self.mode = mode
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0

    def deal_hands(self):
        """Deal 5 cards to each player plus 3 cards to a kitty."""
        for p in self.players:
            p.hand = []
        self.kitty = []

        for p in self.players:
            p.add_to_hand(self.deck.deal(5))
        self.kitty.extend(self.deck.deal(3))

    def set_trump(self, suit):
        self.trump_suit = suit

    # Add other game logic methods (bidding, playing tricks, etc.) as needed...

#################################
#            ROUTES             #
#################################

@app.route("/", methods=["GET"])
def home():
    """
    The default route so we don't get a 404 at the root.
    Visiting https://fortyfives.onrender.com/ will return this message.
    """
    return (
        "<h2>Welcome to the 'Forty-Fives' Card Game API!</h2>"
        "<p>Use POST requests to /set_mode, /deal_cards, etc.</p>"
    )

@app.route("/set_mode", methods=["POST"])
def set_mode():
    """
    Example: Set the game mode to 'headsup' or some other mode you may implement.
    """
    global game_mode, current_game
    data = request.get_json() or {}
    mode = data.get("mode", "headsup")
    game_mode = mode
    current_game = Game(mode)
    return jsonify({"message": f"Game mode set to {mode}", "mode": mode})

@app.route("/deal_cards", methods=["POST"])
def deal_cards():
    """
    Example: Deal the cards for the current game.
    """
    global current_game
    if not current_game:
        return jsonify({"error": "No current game. Set game mode first (/set_mode)."}), 400
    
    current_game.deal_hands()
    return jsonify({
        "player_hand": [str(c) for c in current_game.players[0].hand],
        "kitty_size": len(current_game.kitty),
        "message": "Cards dealt."
    })

@app.route("/set_trump", methods=["POST"])
def set_trump():
    """
    Example: Set a trump suit for the current game.
    """
    global current_game
    if not current_game:
        return jsonify({"error": "No current game. Set game mode first (/set_mode)."}), 400
    
    data = request.get_json() or {}
    suit = data.get("suit", "Hearts")
    current_game.set_trump(suit)
    return jsonify({"message": f"Trump suit set to {suit}", "trump_suit": suit})

# You can add more routes here for the rest of the game’s flow, e.g.:
# /submit_bid, /play_trick, etc.

#################################
#        APP ENTRY POINT        #
#################################

if __name__ == "__main__":
    # On Render, you typically won't run `python main.py` manually;
    # Instead, you set a Start Command in the Render dashboard like: 
    #   gunicorn main:app
    # (assuming this file is named "main.py" and the Flask instance is "app")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
