import os
import random
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

game_mode = None    # Currently only "headsup" is supported
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
        # Ensure 5 of Hearts is present
        if not any(str(c) == "5 of Hearts" for c in self.cards):
            self.cards.append(Card("Hearts", "5"))
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self, num):
        dealt = self.cards[:num]
        self.cards = self.cards[num:]
        return dealt

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
    def set_hand(self, cards):
        self.hand = cards

class Game:
    def __init__(self, mode):
        self.mode = mode
        # For Heads Up, we have two players: "You" and "Computer"
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
    def deal_hands(self):
        self.deck.shuffle()
        for player in self.players:
            player.set_hand(self.deck.deal(5))
    def get_player_hand(self):
        return [str(card) for card in self.players[0].hand]
    def get_dealer(self):
        # For this simple version, we consider the human ("You") as the dealer.
        return self.players[0].name

#################################
#           ROUTES              #
#################################

# Landing page: Select game mode.
@app.route("/", methods=["GET"])
def landing():
    landing_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>45's Card Game - Select Mode</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; margin-top: 100px; }
        .mode-btn { padding: 10px 20px; margin: 10px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer; }
      </style>
    </head>
    <body>
      <h1>Welcome to 45's Card Game</h1>
      <p>Select Game Mode:</p>
      <button class="mode-btn" onclick="setMode('headsup')">Heads Up</button>
      <script>
        async function setMode(mode) {
          const response = await fetch('/set_mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode })
          });
          if(response.ok){
            window.location.href = '/game';
          } else {
            alert('Error setting mode.');
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

# Main game UI: Contains the "Deal Cards" button.
@app.route("/game", methods=["GET"])
def game_ui():
    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>45's Card Game</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; margin-top: 50px; }
        #gameContainer { max-width: 800px; margin: auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; margin: 10px; }
      </style>
    </head>
    <body>
      <div id="gameContainer">
        <h1>45's Card Game - Heads Up</h1>
        <p>Dealer: <span id="dealer"></span></p>
        <button id="dealCardsButton">Deal Cards</button>
        <div id="hand"></div>
      </div>
      <script>
        document.getElementById("dealCardsButton").addEventListener("click", async function(){
          const response = await fetch('/deal_cards', { method: 'POST' });
          const data = await response.json();
          if(data.error) {
            alert(data.error);
            return;
          }
          document.getElementById("dealer").innerText = data.dealer;
          document.getElementById("hand").innerHTML = "<h3>Your Hand:</h3><p>" + data.player_hand.join(", ") + "</p>";
        });
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
    # Log to console for debugging.
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
