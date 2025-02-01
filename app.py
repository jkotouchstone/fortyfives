import os
import random
import time
from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# For now, only "headsup" mode is supported.
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
        # Ensure the special 5 of Hearts is in the deck.
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
        self.hand = []       # List of Card objects
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = [] # Collected cards from won tricks
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def get_hand_strings(self):
        return [str(card) for card in self.hand]
    def discard_auto(self, trump):
        # Automatically discard all non-trump cards.
        before = len(self.hand)
        self.hand = [card for card in self.hand if card.suit == trump]
        return before - len(self.hand)

class Game:
    def __init__(self, mode):
        self.mode = mode  # Only "headsup" is implemented
        self.players = self.initialize_players(mode)
        self.deck = Deck()
        self.kitty = []         # 3 cards set aside
        self.trump_suit = None  # Set later during trump selection
        self.bid_winner = None  # 0 = human (dealer), 1 = computer
        self.bid = 0            # Winning bid amount
        self.leading_player = None  # Which player leads the trick: 0 or 1
        self.trick_count = 0
        self.trick_log_text = ""
        self.current_lead_suit = None
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trick_history = []  # List of dictionaries, one per trick
    def initialize_players(self, mode):
        if mode == "headsup":
            return [Player("You"), Player("Computer")]
        return [Player("You"), Player("Computer")]
    def deal_hands(self):
        self.deck.shuffle()
        self.kitty = self.deck.deal(3)
        for p in self.players:
            p.hand = []
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
        # In this demo, the human is always the dealer.
        return self.players[0].name
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_phase(self, bidder_index, discards):
        # Remove manually selected discard cards (list of strings) from bidder's hand.
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
                    bidder.hand.append(c)
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": self.get_player_hand()}
    def play_trick(self, played_card=None):
        # Trick play for Heads Up.
        played = {}
        if self.leading_player == 1:  # Computer leads
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
                        p.score += BONUS_POINTS
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
    <html>
    <head>
      <title>45's Card Game - Select Mode</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; margin-top: 100px; }
        .mode-btn { padding: 10px 20px; font-size: 18px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
      </style>
    </head>
    <body>
      <h1>Welcome to 45's Card Game</h1>
      <p>Select Game Mode:</p>
      <button class="mode-btn" onclick="setMode('headsup')">Heads Up</button>
      <script>
        async function setMode(mode) {
          const res = await fetch('/set_mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode: mode})
          });
          if(res.ok){
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
        #gameContainer { max-width: 1000px; margin: 50px auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }
        .btn { padding: 10px 20px; font-size: 16px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
        .card-row { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }
        .card-image { width: 100px; }
      </style>
    </head>
    <body>
      <div id="gameContainer">
        <h1>45's Card Game - Heads Up</h1>
        <p>Dealer: <span id="dealer"></span></p>
        <button class="btn" id="dealCardsButton">Deal Cards</button>
        <div id="hand" class="card-row"></div>
      </div>
      <script>
        document.getElementById("dealCardsButton").addEventListener("click", async function(){
          const res = await fetch('/deal_cards', { method: 'POST' });
          const data = await res.json();
          if(data.error){
            alert(data.error);
            return;
          }
          document.getElementById("dealer").innerText = data.dealer;
          const handDiv = document.getElementById("hand");
          handDiv.innerHTML = "<h3>Your Hand:</h3>";
          data.player_hand.forEach(card => {
            const img = document.createElement("img");
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
          const rank_code = rank === "10" ? "0" : (["J", "Q", "K", "A"].includes(rank) ? rank : rank);
          const suit_code = suit[0].upperCase ? suit[0].upperCase() : suit[0].toUpperCase(); // Ensure uppercase.
          return `https://deckofcardsapi.com/static/img/${rank_code}${suit_code}.png`;
        }
        // Alternatively, simply use:
        function getCardImageUrl(card) {
          const parts = card.split(" of ");
          if(parts.length !== 2) return "";
          let [rank, suit] = parts;
          let rank_code = rank === "10" ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
          let suit_code = suit[0].toUpperCase();
          return `https://deckofcardsapi.com/static/img/${rank_code}${suit_code}.png`;
        }
      </script>
    </body>
    </html>
    """
    return render_template_string(game_html)

# Deal cards endpoint.
@app.route("/deal_cards", methods=["POST"])
def deal_cards_route():
    global current_game
    if current_game is None:
        return jsonify({"error": "Game mode not set. Please select a game mode."}), 400
    current_game.deal_hands()
    current_game.starting_scores = {p.name: p.score for p in current_game.players}
    # Clear previous trump and trick history.
    current_game.trump_suit = None
    current_game.trick_history = []
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
