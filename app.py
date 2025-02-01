import os
import random
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

#########################
#       GAME LOGIC      #
#########################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g., "Hearts"
        self.rank = rank  # e.g., "A", "7", etc.

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self, num_decks=1):
        self.suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = []
        for _ in range(num_decks):
            for s in self.suits:
                for r in self.ranks:
                    self.cards.append(Card(s, r))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

def get_card_image_url(card):
    """Returns a URL to an image for a given card."""
    rank_code = "0" if card.rank == "10" else card.rank.upper()[:1]  # '10' => '0', 'K' => 'K'
    suit_code = card.suit[0].upper()  # 'Hearts' => 'H', 'Spades' => 'S', ...
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

def get_card_rank_value(card, trump_suit=None):
    """
    Return a numeric rank value for card. 
    Simple approach: base rank + 100 if it's trump, else +0.
    You can add more special cases (e.g., '5 of Hearts') if needed.
    """
    base_values = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, 
        "7": 7, "8": 8, "9": 9, "10": 10, 
        "J": 11, "Q": 12, "K": 13, "A": 14
    }
    value = base_values.get(card.rank, 0)
    if card.suit == trump_suit:
        value += 100
    return value

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = [Player("You"), Player("Computer")]
        self.trump_suit = None
        self.bid_winner_index = 0
        self.current_leader_index = 0
        self.trick_count = 0
        self.kitty = []

    def deal(self):
        """Deal hands and prepare kitty."""
        for p in self.players:
            p.hand = []
        self.kitty = []

        # Example: 5-card hands + 3-card kitty
        for p in self.players:
            p.hand.extend(self.deck.deal(5))
        self.kitty.extend(self.deck.deal(3))

    def set_trump(self, suit):
        self.trump_suit = suit

    def play_trick(self, card_str):
        """
        Example of a simplified trick flow:
         - If it's human's lead, parse the card played,
           remove from hand, let the computer respond.
         - Decide winner. Update scores.
         - Return the new game state.
        """
        result_text = ""

        # Human's card
        human_player = self.players[0]
        card_to_play = next((c for c in human_player.hand if str(c) == card_str), None)
        if not card_to_play:
            return {"error": "Invalid card choice."}

        human_player.hand.remove(card_to_play)
        result_text += f"You played {card_to_play}. "

        # Computer picks a card (simple random here)
        comp_player = self.players[1]
        if not comp_player.hand:
            # Edge case: computer has no cards
            comp_card = None
            result_text += "Computer has no card to play."
        else:
            comp_card = random.choice(comp_player.hand)
            comp_player.hand.remove(comp_card)
            result_text += f"Computer played {comp_card}. "

        # Determine winner
        human_val = get_card_rank_value(card_to_play, self.trump_suit)
        comp_val = get_card_rank_value(comp_card, self.trump_suit) if comp_card else -1
        winner_index = 0 if human_val > comp_val else 1

        self.players[winner_index].score += 5
        self.players[winner_index].tricks_won += 1
        result_text += f"Winner: {self.players[winner_index].name}!"

        # Return updated info
        return {
            "result_text": result_text,
            "player_hand": [str(c) for c in self.players[0].hand],
            "player_score": self.players[0].score,
            "computer_score": self.players[1].score
        }

#########################
#       FLASK ROUTES    #
#########################

current_game = None

@app.route("/set_mode", methods=["POST"])
def set_mode():
    # If you had multiple game modes, handle them here
    global current_game
    current_game = Game()
    return jsonify({"status": "New game created."})

@app.route("/deal_cards", methods=["POST"])
def deal_cards():
    global current_game
    if not current_game:
        return jsonify({"error": "No game in progress."}), 400

    current_game.deal()
    return jsonify({
        "player_hand": [str(c) for c in current_game.players[0].hand],
        "kitty_cards_count": len(current_game.kitty)
    })

@app.route("/select_trump", methods=["POST"])
def select_trump():
    global current_game
    if not current_game:
        return jsonify({"error": "No game in progress."}), 400

    data = request.json
    trump_suit = data.get("trump_suit", "Hearts")
    current_game.set_trump(trump_suit)
    return jsonify({"trump_suit": trump_suit})

@app.route("/play_trick", methods=["POST"])
def play_trick():
    global current_game
    if not current_game:
        return jsonify({"error": "No game in progress."}), 400

    data = request.json
    card_str = data.get("played_card")
    result = current_game.play_trick(card_str)
    return jsonify(result)

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
