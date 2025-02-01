import os
import random
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# We support only the "45's Heads Up" game in this version.
game_mode = None
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
        self.mode = mode  # Only "headsup" mode is supported
        # In Heads Up, we have two players: the human ("You") and the computer.
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.set_hand(self.deck.deal(5))
    def get_player_hand(self):
        return self.players[0].get_hand_strings()
    def get_dealer(self):
        # For this simple version, the human is always the dealer.
        return self.players[0].name

#################################
#         UTILITY FUNCTION      #
#################################

def getCardImageUrl(card):
    """
    Given a card string (e.g., "A of Hearts"), returns the URL for its image.
    The Deck of Cards API uses a 0 for 10 and uppercase suit letter.
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

# Landing page: Select Game Mode.
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
      <button class="btn" onclick="setMode('headsup')">45's Heads Up</button>
      <script>
        async function setMode(mode) {
          const res = await fetch('/set_mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ mode: mode })
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
def set_mode_route():
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
        <h1>45's Heads Up</h1>
        <p>Dealer: <span id="dealer"></span></p>
        <button class="btn" id="dealCardsBtn">Deal Cards</button>
        <div id="hand" class="card-row"></div>
      </div>
      <script>
        async function sendRequest(url, data = {}) {
          try {
            const res = await fetch(url, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(data)
            });
            if (!res.ok) {
              const err = await res.json();
              return { error: err.error || "Error" };
            }
            return await res.json();
          } catch (err) {
            console.error("Network error:", err);
            return { error: err.message };
          }
        }
        function getCardImageUrl(card) {
          const parts = card.split(" of ");
          if (parts.length !== 2) return "";
          let [rank, suit] = parts;
          let rank_code = rank === "10" ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
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
        document.getElementById("dealCardsBtn").addEventListener("click", async () => {
          const data = await sendRequest("/deal_cards");
          if (data.error) {
            alert(data.error);
            return;
          }
          document.getElementById("dealer").innerText = data.dealer;
          renderHand("hand", data.player_hand);
        });
      </script>
    </body>
    </html>
    """
    return render_template_string(game_html)

# Endpoint to deal cards.
@app.route("/deal_cards", methods=["POST"])
def deal_cards():
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

# Serve static files if needed.
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
