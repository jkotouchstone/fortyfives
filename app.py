import os
import random
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# We support only 45's Heads Up in this version.
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
        self.hand = []  # List of Card objects
    def set_hand(self, cards):
        self.hand = cards
    def get_hand_strings(self):
        return [str(card) for card in self.hand]

class Game:
    def __init__(self):
        # Heads Up: two players – human ("You") and computer.
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        # (For now we are not using kitty/trump/discard/trick play.)
        self.bid_winner = None  # 0 = human (dealer), 1 = computer
        self.bid = 0
    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.set_hand([])
        for p in self.players:
            p.set_hand(self.deck.deal(5))
    def get_player_hand(self):
        return self.players[0].get_hand_strings()
    def get_dealer(self):
        # In this simple version, the human ("You") is always the dealer.
        return self.players[0].name

#################################
#         UTILITY FUNCTION      #
#################################

def getCardImageUrl(card):
    """
    Given a card string like "A of Hearts", returns the URL for its image.
    The Deck of Cards API uses a "0" for 10 and an uppercase suit letter.
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

# Landing page – no mode selection; only Heads Up is supported.
@app.route("/", methods=["GET"])
def landing():
    global current_game
    current_game = Game()
    current_game.deal_hands()
    dealer = current_game.get_dealer()
    # The bidding section is included below.
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
        .btn { padding: 10px 20px; font-size: 16px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
        .section { margin: 20px 0; display: none; }
      </style>
    </head>
    <body>
      <div id="gameContainer">
        <h1>45's Heads Up</h1>
        <p>Dealer: <span id="dealer">""" + dealer + """</span></p>
        <h2>Your Hand:</h2>
        <div id="hand" class="card-row"></div>
        <div id="biddingSection" class="section">
          <h2>Bidding</h2>
          <p id="computerBid"></p>
          <div id="bidButtons">
            <button class="btn bidButton" data-bid="0">Pass</button>
            <button class="btn bidButton" data-bid="15">15</button>
            <button class="btn bidButton" data-bid="20">20</button>
            <button class="btn bidButton" data-bid="25">25</button>
            <button class="btn bidButton" data-bid="30">30</button>
          </div>
          <p id="bidError"></p>
        </div>
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
        async function initGame() {
          // Render player's hand from the server-side auto-deal.
          // (The server already dealt the hand.)
          const playerHand = """ + str(current_game.get_player_hand()) + """;
          renderHand("hand", playerHand);
          // Now fetch the computer's bid.
          const compBidResp = await sendRequest("/computer_first_bid");
          if(compBidResp && !compBidResp.error) {
            document.getElementById("computerBid").innerText = "Computer's bid: " + compBidResp.computer_bid;
            // Enable only valid bid options.
            document.querySelectorAll(".bidButton").forEach(btn => {
              const bidVal = parseInt(btn.getAttribute("data-bid"));
              if(compBidResp.computer_bid == 15){
                btn.disabled = (bidVal !== 0 && bidVal !== 20);
              } else if(compBidResp.computer_bid == 20){
                btn.disabled = (bidVal !== 0 && bidVal !== 25);
              } else if(compBidResp.computer_bid == 25){
                btn.disabled = (bidVal !== 0 && bidVal !== 30);
              }
            });
            // Show bidding section.
            document.getElementById("biddingSection").style.display = "block";
          }
        }
        // Set up event listeners for bidding buttons.
        document.querySelectorAll(".bidButton").forEach(btn => {
          btn.addEventListener("click", async () => {
            btn.classList.add("selected-card");
            const bidValue = parseInt(btn.getAttribute("data-bid"));
            const compBidText = document.getElementById("computerBid").innerText;
            const compBid = compBidText ? parseInt(compBidText.replace("Computer's bid: ", "")) : 0;
            const result = await sendRequest("/submit_bid", { player_bid: bidValue, computer_bid: compBid });
            if(result.error){
              document.getElementById("bidError").innerText = result.error;
              return;
            }
            // For this demo, simply alert the bid outcome.
            alert("Bid submitted. Outcome: " + result.bid_winner);
          });
        });
        // Initialize the game on page load.
        window.addEventListener("load", initGame);
      </script>
    </body>
    </html>
    """
    return render_template_string(game_html)

@app.route("/computer_first_bid", methods=["POST"])
def computer_first_bid():
    # For demonstration, randomly choose one of the valid bids.
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def submit_bid():
    # Basic bidding logic for demonstration.
    # If computer bids 30, bidding stops.
    data = request.get_json()
    player_bid = data.get("player_bid")
    comp_bid = data.get("computer_bid")
    if comp_bid == 30:
        # Computer wins the bid.
        return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer"})
    # If computer bids 0, you must bid 15.
    if comp_bid == 0:
        if player_bid != 15:
            return jsonify({"error": "Invalid bid. When opponent passes, you must bid 15."}), 400
        else:
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})
    let_bid = comp_bid + 5
    if player_bid == 0:
        return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer"})
    elif player_bid != let_bid:
        return jsonify({"error": f"Invalid bid. You must either pass (0) or bid {let_bid}."}), 400
    else:
        return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})

# Serve static files if needed.
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
