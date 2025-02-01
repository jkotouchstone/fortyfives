import os
import random
import time
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# We only support the 45's Heads Up game in this version.
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
        self.hand = []         # List of Card objects
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []   # Collected cards from won tricks
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def set_hand(self, cards):
        self.hand = cards
    def get_hand_strings(self):
        return [str(card) for card in self.hand]
    def discard_auto(self, trump):
        before = len(self.hand)
        self.hand = [card for card in self.hand if card.suit == trump]
        return before - len(self.hand)

class Game:
    def __init__(self, mode):
        self.mode = mode  # Only "headsup" is supported.
        # In Heads Up, we have two players: human ("You") and computer.
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
        # In this simple demo, the human ("You") is always the dealer.
        return self.players[0].name
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_phase(self, bidder_index, discards):
        # Remove selected discard cards (list of strings) from bidder's hand.
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
                    bidder.hand.append(c)
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": self.get_player_hand()}
    def play_trick(self, played_card=None):
        # Trick play for Heads Up.
        played = {}
        if self.leading_player == 1:  # Computer leads.
            if played_card is None:
                comp_hand = self.players[1].hand
                trump_cards = [card for card in comp_hand if card.suit == self.trump_suit]
                if trump_cards:
                    trump_cards.sort(key=lambda card: get_card_rank(str(card), trump=self.trump_suit), reverse=True)
                    comp_card = trump_cards[0]
                    comp_hand.remove(comp_card)
                else:
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
            if human_card and human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
                winner = "You"
            else:
                r_human = get_card_rank(str(human_card), trump=self.trump_suit) if human_card else -1
                r_comp = get_card_rank(str(comp_card), trump=self.trump_suit) if comp_card else -1
                winner = "You" if r_human > r_comp else "Computer"
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
                comp_card = random.choice(comp_hand)
                comp_hand.remove(comp_card)
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
                r_human = get_card_rank(str(human_card), trump=self.trump_suit) if human_card else -1
                r_comp = get_card_rank(str(comp_card), trump=self.trump_suit) if comp_card else -1
                winner = "You" if r_human > r_comp else "Computer"
            self.players[0 if winner=="You" else 1].score += 5
            self.players[0 if winner=="You" else 1].tricks_won += 1
            trick_info = {"trick_number": self.trick_count + 1,
                          "cards": current_trick,
                          "winner": winner}
            self.trick_history.append(trick_info)
            self.leading_player = 0 if winner=="You" else 1
        self.trick_count += 1
        if self.trick_count >= 5 or len(self.players[0].hand) == 0:
            # Bonus logic (for demonstration purposes)
            best_card = None
            best_player = None
            best_val = -1
            for p in self.players:
                for card in p.trick_pile:
                    val = get_card_rank(card, trump=self.trump_suit)
                    if val > best_val:
                        best_val = val
                        best_card = card
                        best_player = p.name
            bonus_text = ""
            if best_player:
                bonus_text = f" Bonus: Highest card was {best_card} (won by {best_player})."
                for p in self.players:
                    if p.name == best_player:
                        p.score += 5  # BONUS_POINTS
                        break
            hand_scores = {p.name: p.score - self.starting_scores[p.name] for p in self.players}
            result_text = self.trick_log_text + bonus_text + f" Hand complete. Last trick won by {self.trick_history[-1]['winner']}."
            return {"trick_result": result_text, "current_trick_cards": current_trick, "trick_history": self.trick_history}, hand_scores
        else:
            return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick, "trick_winner": winner}, None

#################################
#           ROUTES              #
#################################

# Landing page.
@app.route("/", methods=["GET"])
def landing():
    landing_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Card Game - Select Mode</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; margin-top: 100px; }
        .mode-btn { padding: 10px 20px; margin: 10px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer; }
      </style>
    </head>
    <body>
      <h1>Welcome to 45's Card Game</h1>
      <p>Select Game Mode:</p>
      <button class="mode-btn" onclick="setMode('headsup')">45's Heads Up</button>
      <script>
        async function setMode(mode) {
          const res = await fetch('/set_mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode })
          });
          if (res.ok){
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

# Set game mode endpoint.
@app.route("/set_mode", methods=["POST"])
def api_set_mode():
    global game_mode, current_game
    data = request.get_json()
    mode = data.get("mode", "headsup")
    game_mode = mode
    current_game = Game(mode)
    return jsonify({"mode": mode})

# Main game UI.
@app.route("/game", methods=["GET"])
def api_game_ui():
    # On load, automatically deal a new hand.
    # The game page also includes the full game flow sections (bidding, trump, kitty, discard, trick).
    # (They will be hidden until needed.)
    game_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Card Game</title>
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
        <h1>45's Card Game - Heads Up</h1>
        <div id="scoreBoard">Player: 0 | Computer: 0</div>
        <div id="trumpDisplay"></div>
        <div>
          <h2>Dealer: <span id="dealer"></span></h2>
        </div>
        <div id="playerHandSection">
          <h2>Your Hand</h2>
          <div id="playerHand" class="card-row"></div>
        </div>
        <!-- The additional game flow sections (bidding, trump selection, kitty, discard, trick) remain here -->
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
        <div id="trumpSelectionSection" class="section">
          <h2>Select Trump Suit</h2>
          <div style="display: flex; justify-content: center; gap: 20px;">
            <button class="btn trumpButton" data-suit="Hearts" style="background-color:#e74c3c;">♥</button>
            <button class="btn trumpButton" data-suit="Diamonds" style="background-color:#f1c40f;">♦</button>
            <button class="btn trumpButton" data-suit="Clubs" style="background-color:#27ae60;">♣</button>
            <button class="btn trumpButton" data-suit="Spades" style="background-color:#2980b9;">♠</button>
          </div>
        </div>
        <div id="kittySection" class="section">
          <h2>Kitty Cards</h2>
          <p id="kittyPrompt">Click "Reveal Kitty" to see the kitty.</p>
          <div id="kittyCards" class="card-row"></div>
          <button class="btn" id="revealKittyButton">Reveal Kitty</button>
          <button class="btn" id="submitKittyButton" style="display:none;">Submit Kitty Selection</button>
        </div>
        <div id="discardSection" class="section">
          <h2>Discard Phase</h2>
          <p id="discardMessage">Select cards to discard (0-4):</p>
          <div id="discardHand" class="card-row"></div>
          <p id="discardCount">Discarding 0 card(s)</p>
          <button class="btn" id="skipDiscardButton">Submit Discards</button>
          <p id="computerDiscardInfo"></p>
        </div>
        <div id="trickSection" class="section">
          <h2>Trick Phase</h2>
          <div id="currentTrick" class="card-row"></div>
          <p id="playPrompt"></p>
          <button class="btn" id="playTrickButton">Play Selected Card</button>
        </div>
        <div id="trickPiles" style="display: flex; justify-content: space-around; margin-top:20px;">
          <div id="dealerTrickPile" class="pile">
            <h3>Dealer's Tricks</h3>
          </div>
          <div id="playerTrickPile" class="pile">
            <h3>Your Tricks</h3>
          </div>
        </div>
      </div>
      <footer style="text-align: center; margin-top: 20px;">&copy; O'Donohue Software</footer>
      <script>
        // Auto-deal new hand on page load.
        window.addEventListener("load", async () => {
          const data = await sendRequest("/deal_cards");
          if(data.error) {
            alert(data.error);
            return;
          }
          document.getElementById("dealer").innerText = data.dealer;
          renderHand("playerHand", data.player_hand);
          // (At this point, further game flow like bidding can be initiated.)
          showSection("playerHandSection");
          // For demonstration, automatically request computer's bid.
          const compBidResp = await sendRequest("/computer_first_bid");
          if(compBidResp && !compBidResp.error){
            document.getElementById("computerBid").innerText = `Computer's bid: ${compBidResp.computer_bid}`;
            // Here, further bidding UI logic would be added.
            showSection("biddingSection");
          }
        });

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
          if(parts.length !== 2) return "";
          let [rank, suit] = parts;
          let rank_code = rank === "10" ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
          let suit_code = suit[0].toUpperCase();
          return `https://deckofcardsapi.com/static/img/${rank_code}${suit_code}.png`;
        }
        function getCardBackUrl() {
          return "https://deckofcardsapi.com/static/img/back.png";
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
        function renderKittyCards(containerId, kitty_list) {
          const container = document.getElementById(containerId);
          container.innerHTML = "";
          kitty_list.forEach(card => {
            const img = document.createElement("img");
            img.src = getCardBackUrl();
            img.alt = card;
            img.className = "card-image";
            img.addEventListener("click", () => {
              img.classList.toggle("selected-card");
            });
            container.appendChild(img);
          });
        }
        function showSection(id) {
          document.getElementById(id).style.display = "block";
        }
        function hideSection(id) {
          document.getElementById(id).style.display = "none";
        }
        function updateTrumpDisplay(suit) {
          const suitSymbols = { "Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠" };
          document.getElementById("trumpDisplay").innerHTML = `<span>Trump: <span style="font-size:48px;">${suitSymbols[suit]}</span></span>`;
        }
        function addTrickToPile(trickCards, winner) {
          const pileId = winner === "You" ? "playerTrickPile" : "dealerTrickPile";
          const pile = document.getElementById(pileId);
          trickCards.forEach(card => {
            const img = document.createElement("img");
            img.src = getCardImageUrl(card);
            img.alt = card;
            img.className = "card-image";
            img.style.width = "40px";
            pile.appendChild(img);
          });
        }
      </script>
    </body>
    </html>
    """
    return render_template_string(game_html)

#################################
#           API ROUTES          #
#################################

@app.route("/set_mode", methods=["POST"])
def api_set_mode():
    global game_mode, current_game
    data = request.get_json()
    mode = data.get("mode", "headsup")
    game_mode = mode
    current_game = Game(mode)
    return jsonify({"mode": mode})

@app.route("/deal_cards", methods=["POST"])
def api_deal_cards():
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

@app.route("/computer_first_bid", methods=["POST"])
def api_computer_first_bid():
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def api_submit_bid():
    try:
        if current_game is None:
            return jsonify({"error": "No game in progress. Set a game mode and deal cards first."}), 400
        data = request.get_json()
        player_bid = data.get("player_bid", None)
        comp_bid = data.get("computer_bid", None)
        if comp_bid is None:
            return jsonify({"error": "Computer bid missing."}), 400
        if comp_bid == 30:
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            current_game.bid_winner = 1
            current_game.bid = comp_bid
            current_game.leading_player = 1
            return jsonify({
                "computer_bid": comp_bid,
                "bid_winner": "Computer",
                "trump_suit": trump_suit,
                "kitty_cards": kitty
            })
        if comp_bid == 0:
            if player_bid != 15:
                return jsonify({"error": "Invalid bid. When opponent passes, you must bid 15."}), 400
            else:
                current_game.bid_winner = 0
                current_game.bid = 15
                current_game.leading_player = 0
                return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})
        let_bid = comp_bid + 5
        if player_bid == 0:
            current_game.bid_winner = 1
            current_game.bid = comp_bid
            current_game.leading_player = 1
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            return jsonify({
                "computer_bid": comp_bid,
                "bid_winner": "Computer",
                "trump_suit": trump_suit,
                "kitty_cards": kitty
            })
        elif player_bid != let_bid:
            return jsonify({"error": f"Invalid bid. You must either pass (0) or bid {let_bid}."}), 400
        else:
            current_game.bid_winner = 0
            current_game.bid = player_bid
            current_game.leading_player = 0
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})
    except Exception as e:
        print("Error in /submit_bid:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/select_trump", methods=["POST"])
def api_select_trump():
    data = request.get_json()
    suit = data.get("trump_suit", "Hearts")
    kitty = current_game.confirm_trump(suit)
    return jsonify({"kitty_cards": kitty, "trump_suit": suit})

@app.route("/discard_and_draw", methods=["POST"])
def api_discard_and_draw():
    data = request.get_json()
    discards = data.get("discarded_cards", None)
    result = current_game.discard_phase(current_game.bid_winner, discards)
    if current_game.bid_winner == 1:
        comp_disc = current_game.players[1].discard_auto(current_game.trump_suit)
        result["computer_discard_count"] = comp_disc
    return jsonify(result)

@app.route("/attach_kitty", methods=["POST"])
def api_attach_kitty():
    data = request.get_json()
    keep_cards = data.get("keep_cards", [])
    bidder = current_game.players[current_game.bid_winner]
    for card_str in keep_cards:
        for c in current_game.kitty:
            if str(c) == card_str:
                bidder.hand.append(c)
    current_game.kitty = [c for c in current_game.kitty if str(c) not in keep_cards]
    return jsonify({"player_hand": current_game.get_player_hand()})

@app.route("/play_trick", methods=["POST"])
def api_play_trick():
    data = request.get_json()
    played_card = data.get("played_card")
    result_obj, hand_scores = current_game.play_trick(played_card)
    resp = {
        "trick_result": result_obj.get("trick_result", ""),
        "current_trick_cards": result_obj.get("current_trick_cards", {}),
        "trick_winner": result_obj.get("trick_winner", ""),
        "player_hand": current_game.get_player_hand(),
        "player_score": current_game.players[0].score,
        "computer_score": {p.name: p.score for p in current_game.players if p.name != "You"},
        "trick_history": current_game.trick_history
    }
    if result_obj.get("computer_card"):
        resp["computer_card"] = result_obj.get("computer_card")
    if hand_scores:
        resp["hand_scores"] = hand_scores
    return jsonify(resp)

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
