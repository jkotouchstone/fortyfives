import os
import random
import time
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# This version supports only 45's Heads Up.
current_game = None

#################################
#         GAME CLASSES          #
#################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit      # e.g., "Hearts"
        self.rank = rank      # e.g., "A", "7", etc.
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        for s in suits:
            for r in ranks:
                self.cards.append(Card(s, r))
        # Ensure special card 5 of Hearts is included.
        if not any(str(c) == "5 of Hearts" for c in self.cards):
            self.cards.append(Card("Hearts", "5"))
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
        self.hand = []         # List of Card objects
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []   # Collected cards from won tricks
    def set_hand(self, cards):
        self.hand = cards
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def get_hand_strings(self):
        return [str(card) for card in self.hand]
    def discard_auto(self, trump):
        before = len(self.hand)
        self.hand = [card for card in self.hand if card.suit == trump]
        return before - len(self.hand)

class Game:
    def __init__(self):
        # Heads Up: two players (human "You" and computer).
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []         # 3 cards set aside
        self.trump_suit = None  # To be chosen during trump selection
        self.bid_winner = None  # 0 = human (dealer), 1 = computer
        self.bid = 0            # Winning bid amount
        self.leading_player = None  # Which player leads the trick: 0 or 1
        self.trick_count = 0
        self.trick_log_text = ""
        self.current_lead_suit = None
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trick_history = []  # List of dicts, one per trick
    def deal_hands(self):
        self.deck.shuffle()
        self.kitty = self.deck.deal(3)
        for p in self.players:
            p.set_hand([])
            p.tricks_won = 0
            p.trick_pile = []
        for p in self.players:
            p.add_to_hand(self.deck.deal(5))
        self.trick_count = 0
        self.trick_log_text = ""
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trick_history = []
        self.trump_suit = None
    def get_player_hand(self):
        return self.players[0].get_hand_strings()
    def get_dealer(self):
        # In this demo, the human ("You") is always the dealer.
        return self.players[0].name
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_phase(self, bidder_index, discards):
        # Remove selected cards (by their string) from bidder's hand.
        bidder = self.players[bidder_index]
        initial = len(bidder.hand)
        bidder.hand = [card for card in bidder.hand if str(card) not in discards]
        discarded = initial - len(bidder.hand)
        return {"player_hand": self.get_player_hand(), "discard_count": discarded}
    def attach_kitty(self, player_index, keep_list):
        # Add selected kitty cards (by their string) to the bidder's hand.
        bidder = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    bidder.add_to_hand([c])
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": self.get_player_hand()}
    def play_trick(self, played_card=None):
        # Basic trick play for demonstration.
        played = {}
        if self.leading_player == 1:  # Computer leads.
            if played_card is None:
                comp_hand = self.players[1].hand
                # For simplicity, computer plays its first card.
                comp_card = comp_hand.pop(0)
                self.current_lead_suit = comp_card.suit
                played[1] = comp_card
                self.trick_log_text = f"Computer leads with {comp_card}."
            else:
                if played_card not in self.get_player_hand():
                    return {"trick_result": "Invalid card played.", "current_trick_cards": {}}, None
                human_card = next(card for card in self.players[0].hand if str(card) == played_card)
                self.players[0].hand.remove(human_card)
                played[0] = human_card
                self.trick_log_text = f"You played {human_card}."
            current_trick = {
                self.players[1].name: str(played.get(1)) if played.get(1) else "",
                self.players[0].name: str(played.get(0)) if played.get(0) else ""
            }
            # Simplified winner: if your card exists and is trump while computer's is not, you win.
            comp_card = played.get(1)
            human_card = played.get(0)
            if human_card and human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
                winner = "You"
            else:
                # Otherwise, compare lexically (for demonstration).
                winner = "You" if str(human_card) > str(comp_card) else "Computer"
            self.players[0 if winner=="You" else 1].score += 5
            self.players[0 if winner=="You" else 1].tricks_won += 1
            trick_info = {"trick_number": self.trick_count + 1,
                          "cards": current_trick,
                          "winner": winner}
            self.trick_history.append(trick_info)
            self.leading_player = 0 if winner=="You" else 1
        else:  # Human leads.
            if played_card is None:
                return {"trick_result": "Your turn to lead.", "current_trick_cards": {}}, None
            if played_card not in self.get_player_hand():
                return {"trick_result": "Invalid card played.", "current_trick_cards": {}}, None
            human_card = next(card for card in self.players[0].hand if str(card) == played_card)
            self.players[0].hand.remove(human_card)
            self.current_lead_suit = human_card.suit
            played[0] = human_card
            self.trick_log_text = f"You lead with {human_card}."
            comp_hand = self.players[1].hand
            if comp_hand:
                comp_card = comp_hand.pop(0)
                played[1] = comp_card
                self.trick_log_text += f" Computer plays {comp_card}."
            else:
                comp_card = None
                self.trick_log_text += " Computer did not play."
            current_trick = {
                self.players[0].name: str(played.get(0)) if played.get(0) else "",
                self.players[1].name: str(played.get(1)) if played.get(1) else ""
            }
            if human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
                winner = "You"
            else:
                winner = "You" if str(human_card) > str(comp_card) else "Computer"
            self.players[0 if winner=="You" else 1].score += 5
            self.players[0 if winner=="You" else 1].tricks_won += 1
            trick_info = {"trick_number": self.trick_count + 1,
                          "cards": current_trick,
                          "winner": winner}
            self.trick_history.append(trick_info)
            self.leading_player = 0 if winner=="You" else 1
        self.trick_count += 1
        # When 5 tricks have been played or your hand is empty, the hand is complete.
        if self.trick_count >= 5 or len(self.players[0].hand) == 0:
            hand_scores = {p.name: p.score - self.starting_scores[p.name] for p in self.players}
            result_text = self.trick_log_text + " Hand complete. Last trick won by " + self.trick_history[-1]["winner"] + "."
            return {"trick_result": result_text, "current_trick_cards": current_trick, "trick_history": self.trick_history}, hand_scores
        else:
            return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick, "trick_winner": winner}, None

#################################
#           ROUTES              #
#################################

# Landing page – no game mode selection needed.
@app.route("/", methods=["GET"])
def landing():
    # Always use 45's Heads Up.
    global current_game
    current_game = Game()
    current_game.deal_hands()
    dealer = current_game.get_dealer()
    # Render the game page.
    game_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Heads Up</title>
      <link rel="icon" href="https://deckofcardsapi.com/static/img/5_of_clubs.png" type="image/png">
      <style>
        body { font-family: Arial, sans-serif; background-color: #35654d; color: #fff; text-align: center; }
        #gameContainer { max-width: 800px; margin: 50px auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }
        .card-row { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }
        .card-image { width: 100px; }
      </style>
    </head>
    <body>
      <div id="gameContainer">
        <h1>45's Heads Up</h1>
        <p>Dealer: <span id="dealer">""" + dealer + """</span></p>
        <h2>Your Hand:</h2>
        <div id="hand" class="card-row"></div>
      </div>
      <script>
        function getCardImageUrl(card) {
          const parts = card.split(" of ");
          if (parts.length !== 2) return "";
          let [rank, suit] = parts;
          let rank_code = rank === "10" ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
          let suit_code = suit[0].toUpperCase();
          return "https://deckofcardsapi.com/static/img/" + rank_code + suit_code + ".png";
        }
        function renderHand(containerId, hand) {
          const container = document.getElementById(containerId);
          container.innerHTML = "";
          hand.forEach(card => {
            const img = document.createElement("img");
            img.src = getCardImageUrl(card);
            img.alt = card;
            img.className = "card-image";
            container.appendChild(img);
          });
        }
        // Render player's hand using data passed from the server.
        const playerHand = """ + str(current_game.get_player_hand()) + """;
        renderHand("hand", playerHand);
      </script>
    </body>
    </html>
    """
    return render_template_string(game_html)

# Serve static files if needed.
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
