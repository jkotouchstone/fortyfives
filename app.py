import os
import random
from flask import Flask, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# In this version, the only game is 45's Heads Up.
current_game = None

#################################
#         GAME CLASSES          #
#################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g., "Hearts"
        self.rank = rank  # e.g., "A", "7", etc.
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
        # Ensure the special 5 of Hearts is included.
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
        self.hand = []  # List of Card objects
    def set_hand(self, cards):
        self.hand = cards
    def get_hand_strings(self):
        return [str(card) for card in self.hand]

class Game:
    def __init__(self):
        # For Heads Up, we have two players: the human ("You") and the computer.
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.set_hand([])  # Clear any previous hand
        # Deal 5 cards each.
        for p in self.players:
            p.set_hand(self.deck.deal(5))
    def get_player_hand(self):
        return self.players[0].get_hand_strings()
    def get_dealer(self):
        # In this simple version, the human is always the dealer.
        return self.players[0].name

#################################
#         UTILITY FUNCTION      #
#################################

def getCardImageUrl(card):
    """
    Given a card string (e.g., "A of Hearts"), returns the URL for its image.
    The Deck of Cards API uses a "0" for 10 and requires an uppercase suit letter.
    For example, "A of Hearts" returns "https://deckofcardsapi.com/static/img/AH.png"
    """
    parts = card.split(" of ")
    if len(parts) != 2:
        return ""
    rank, suit = parts
    rank_code = "0" if rank == "10" else (rank if rank in ["J", "Q", "K", "A"] else rank)
    suit_code = suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

#################################
#           ROUTES              #
#################################

# Landing page – simply displays the game.
@app.route("/", methods=["GET"])
def landing():
    # For this version, we skip game mode selection and directly use 45's Heads Up.
    global current_game
    current_game = Game()      # Always create a new Heads Up game.
    current_game.deal_hands()  # Auto-deal a new hand.
    dealer = current_game.get_dealer()
    # Render the game UI with the player's hand and dealer name.
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
          if(parts.length !== 2) return "";
          let [rank, suit] = parts;
          let rank_code = (rank === "10") ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
          let suit_code = suit[0].toUpperCase();
          return `https://deckofcardsapi.com/static/img/${rank_code}${suit_code}.png`;
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
        // Player's hand data passed from the server as JSON.
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
