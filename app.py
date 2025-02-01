import os
import random
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# We'll support only "headsup" for now.
game_mode = None
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
        # Ensure 5 of Hearts is in the deck.
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
    def __init__(self, mode):
        self.mode = mode  # Currently only "headsup"
        # For Heads Up, we have two players: "You" and "Computer"
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
    def deal_hands(self):
        self.deck.shuffle()
        for player in self.players:
            player.set_hand(self.deck.deal(5))
    def get_player_hand(self):
        return self.players[0].get_hand_strings()
    def get_dealer(self):
        # In this minimal demo, we consider "You" as the dealer.
        return self.players[0].name

#################################
#         UTILITY FUNCTIONS     #
#################################

def getCardImageUrl(card):
    """
    Given a card string like "A of Hearts", return the URL for its image.
    For 10, we use "0" (as per the Deck of Cards API).
    """
    parts = card.split(" of ")
    if len(parts) != 2:
        return ""
    rank, suit = parts
    rank_code = "0" if rank == "10" else (rank if rank in ["J", "Q", "K", "A"] else rank)
    suit_code = suit[0].lower()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

#################################
#           ROUTES              #
#################################

# Landing page for mode selection.
@app.route("/", methods=["GET"])
def landing():
    landing_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>45's Card Game - Select Mode</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; margin-top: 100px; }
        .btn { padding: 10px 20px; font-size: 18px; margin: 10px; cursor: pointer; border: none; border-radius: 5px; }
      </style>
    </head>
    <body>
      <h1>Welcome to 45's Card Game</h1>
      <p>Select Game Mode:</p>
      <button class="btn" onclick="setMode('headsup')">Heads Up</button>
      <script>
        async function setMode(mode) {
          const res = await fetch('/set_mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode: mode})
          });
          if (res.ok) {
            window.location.href = '/game';
          } else {
            alert("Error setting mode.");
          }
        }
      </script>
    </body>
    </html>
    """
    return render_template_string(landing_html)

# Endpoint to set the game mode.
@app.route("/set_mode", methods=["POST"])
def set_mode_endpoint():
    global game_mode, current_game
    data = request.get_json()
    mode = data.get("mode", "headsup")
    game_mode = mode
    current_game = Game(mode)
    return jsonify({"mode": mode})

# Main game UI.
@app.route("/game", methods=["GET"])
def game_ui():
    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>45's Card Game</title>
      <link rel="icon" href="https://deckofcardsapi.com/static/img/5_of_clubs.png" type="image/png">
      <style>
        body { font-family: Arial, sans-serif; background-color: #35654d; color: #fff; text-align: center; }
        #container { max-width: 800px; margin: 50px auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }
        .btn { padding: 10px 20px; font-size: 16px; margin: 10px; cursor: pointer; border: none; border-radius: 5px; }
        .card-row { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }
        .card-image { width: 100px; }
      </style>
    </head>
    <body>
      <div id="container">
        <h1>45's Card Game - Heads Up</h1>
        <p>Dealer: <span id="dealer"></span></p>
        <button class="btn" id="dealBtn">Deal Cards</button>
        <div id="hand" class="card-row"></div>
      </div>
      <script>
        document.getElementById("dealBtn").addEventListener("click", async function() {
          const res = await fetch("/deal_cards", { method: "POST" });
          const data = await res.json();
          if(data.error) { 
            alert(data.error);
            return;
          }
          document.getElementById("dealer").innerText = data.dealer;
          const handDiv = document.getElementById("hand");
          handDiv.innerHTML = "<h3>Your Hand:</h3>";
          data.player_hand.forEach(card => {
            let img = document.createElement("img");
            img.src = getCardImageUrl(card);
            img.alt = card;
            img.className = "card-image";
            handDiv.appendChild(img);
          });
        });
        function getCardImageUrl(card) {
          const parts = card.split(" of ");
          if(parts.length !== 2) return "";
          let [rank, suit] = parts;
          let rank_code = rank === "10" ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
          let suit_code = suit[0].toLowerCase();
          return `https://deckofcardsapi.com/static/img/${rank_code}${suit_code}.png`;
        }
      </script>
    </body>
    </html>
    """
    return render_template_string(game_html)

# Endpoint to deal cards.
@app.route("/deal_cards", methods=["POST"])
def deal_cards_route():
    global current_game
    if current_game is None:
        return jsonify({"error": "Game mode not set. Please select a game mode."}), 400
    current_game.deal_hands()
    dealer = current_game.get_dealer()
    print("Dealt a new hand. Dealer:", dealer)
    return jsonify({
        "player_hand": current_game.get_player_hand(),
        "dealer": dealer,
        "mode": game_mode
    })

# Static file serving (if needed).
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
