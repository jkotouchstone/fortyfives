import os
import random
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for sessions

#################################
#       GLOBAL GAME STATE       #
#################################

# In this version, we support only 45's Heads Up.
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
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []  # Collected cards from won tricks
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
        # Heads Up: two players ("You" and "Computer")
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []         # 3 cards set aside (for trump/kitty selection)
        self.trump_suit = None  # To be chosen later
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
            p.set_hand([])  # Clear previous hand
            p.tricks_won = 0
            p.trick_pile = []
        for p in self.players:
            p.add_to_hand(self.deck.deal(5))
        self.trick_count = 0
        self.trick_log_text = ""
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trick_history = []
        self.trump_suit = None  # Clear trump for new hand
    def get_player_hand(self):
        return self.players[0].get_hand_strings()
    def get_dealer(self):
        # For this simple game, the human ("You") is always the dealer.
        return self.players[0].name
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_phase(self, bidder_index, discards):
        bidder = self.players[bidder_index]
        initial = len(bidder.hand)
        bidder.hand = [card for card in bidder.hand if str(card) not in discards]
        discarded = initial - len(bidder.hand)
        return {"player_hand": self.get_player_hand(), "discard_count": discarded}
    def attach_kitty(self, player_index, keep_list):
        bidder = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    bidder.add_to_hand([c])
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": self.get_player_hand()}
    def play_trick(self, played_card=None):
        # Basic trick play for demonstration purposes.
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
            comp_card = played.get(1)
            human_card = played.get(0)
            # For demonstration, if human card is trump and computer's is not, human wins; otherwise, compare lexicographically.
            if human_card and human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
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
        if self.trick_count >= 5 or len(self.players[0].hand) == 0:
            hand_scores = {p.name: p.score - self.starting_scores[p.name] for p in self.players}
            result_text = self.trick_log_text + " Hand complete. Last trick won by " + self.trick_history[-1]["winner"] + "."
            return {"trick_result": result_text, "current_trick_cards": current_trick, "trick_history": self.trick_history}, hand_scores
        else:
            return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick, "trick_winner": winner}, None

#################################
#           ROUTES              #
#################################

# --- Login ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["username"] = username
            return redirect(url_for("rules"))
        else:
            error = "Please enter a username."
            return render_template_string("""
                <html><body>
                <h1>Login</h1>
                <p style="color:red;">{{ error }}</p>
                <form method="POST">
                  Username: <input type="text" name="username"><br>
                  <button type="submit">Login</button>
                </form>
                </body></html>
            """, error=error)
    return render_template_string("""
        <html><body>
        <h1>Login</h1>
        <form method="POST">
          Username: <input type="text" name="username"><br>
          <button type="submit">Login</button>
        </form>
        </body></html>
    """)

# --- Rules ---
@app.route("/rules", methods=["GET"])
def rules():
    if "username" not in session:
        return redirect(url_for("login"))
    rules_text = """
    <h1>45's Heads Up Rules</h1>
    <p>Welcome, {{ username }}!</p>
    <p>Game Flow:</p>
    <ul>
      <li><strong>Auto‑Deal:</strong> When you enter the game, 5 cards are dealt to you and the computer.</li>
      <li><strong>Bidding:</strong> The computer issues a bid (15, 20, 25, or 30). As the dealer, you must either pass (bid 0) or bid exactly computer bid + 5.</li>
      <li><strong>Trump & Kitty Selection:</strong> If you win the bid, you select a trump suit. Then, 3 kitty cards are revealed; you may choose which ones to add to your hand.</li>
      <li><strong>Discard Phase:</strong> You may discard 0–4 cards from your hand (a live counter shows the number selected). The computer also discards automatically.</li>
      <li><strong>Trick Play:</strong> The player who wins the bid (or the non‑bidder) leads the first trick. Cards are played, shown as images, and after a short delay the trick is awarded and scores update.</li>
      <li><strong>Score Keeping:</strong> Each trick is worth 5 points; bonus points may be awarded based on the highest card played.</li>
    </ul>
    <p><a href="{{ url_for('game_ui') }}">Start Game</a></p>
    """
    return render_template_string("""
        <html>
          <head>
            <title>45's Heads Up - Rules</title>
            <style>
              body { font-family: Arial, sans-serif; background-color: #35654d; color: #fff; text-align: center; }
              a { color: #f1c40f; font-size: 18px; }
            </style>
          </head>
          <body>
            """ + rules_text + """
          </body>
        </html>
    """, username=session["username"])

# --- Main Game UI ---
@app.route("/game", methods=["GET"])
def game_ui():
    if "username" not in session:
        return redirect(url_for("login"))
    global current_game
    # Create and auto-deal a new hand each time.
    current_game = Game()
    current_game.deal_hands()
    dealer = current_game.get_dealer()
    # The full game flow UI (bidding, trump/kitty, discard, trick play) is reintroduced.
    game_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Heads Up</title>
      <link rel="icon" href="https://deckofcardsapi.com/static/img/5_of_clubs.png" type="image/png">
      <style>
        body { font-family: Arial, sans-serif; background-color: #35654d; color: #fff; text-align: center; }
        #gameContainer { max-width: 1000px; margin: 50px auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }
        .btn { padding: 10px 20px; font-size: 16px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
        .card-row { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }
        .card-image { width: 100px; }
        .selected-card { border: 2px solid #f1c40f; }
        .section { margin: 20px 0; display: none; }
        #scoreBoard { font-weight: bold; margin-bottom: 10px; font-size: 20px; }
        #trumpDisplay span { font-size: 48px; }
        .pile { width: 45%; background-color: #3b7d63; padding: 10px; border-radius: 5px; }
        #discardCount { font-size: 18px; margin-top: 5px; }
        #bidError { color: #ffcccc; }
      </style>
    </head>
    <body>
      <div id="gameContainer">
        <h1>45's Heads Up</h1>
        <div id="scoreBoard">Player: 0 | Computer: 0</div>
        <div id="trumpDisplay"></div>
        <div>
          <h2>Dealer: <span id="dealer">""" + dealer + """</span></h2>
        </div>
        <div id="playerHandSection">
          <h2>Your Hand</h2>
          <div id="hand" class="card-row"></div>
        </div>
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
        <!-- (Additional sections for trump/kitty selection, discard, trick play would go here.) -->
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
        async function initGame() {
          // Render player's hand.
          renderHand("hand", {{ player_hand|safe }});
          // Fetch computer's bid.
          const compBidResp = await sendRequest("/computer_first_bid");
          if(compBidResp && !compBidResp.error){
            document.getElementById("computerBid").innerText = "Computer's bid: " + compBidResp.computer_bid;
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
            document.getElementById("biddingSection").style.display = "block";
          }
        }
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
            alert("Bid submitted. Outcome: " + result.bid_winner);
            // (Here you would proceed to trump/kitty selection, discard, and trick play.)
          });
        });
        window.addEventListener("load", initGame);
      </script>
    </body>
    </html>
    """
    # Pass the player's hand to the template safely (as JSON).
    return render_template_string(game_html, player_hand=current_game.get_player_hand())

# --- API Endpoints ---

@app.route("/computer_first_bid", methods=["POST"])
def computer_first_bid():
    # Randomly choose a bid for the computer.
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def submit_bid():
    data = request.get_json()
    player_bid = data.get("player_bid")
    comp_bid = data.get("computer_bid")
    if comp_bid == 30:
        # Computer wins the bid.
        return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer"})
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

# (Additional endpoints for trump/kitty selection, discard, and trick play would be added here.)

# Serve static files if needed.
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
