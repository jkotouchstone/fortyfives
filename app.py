import os
from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
import random
import time

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# Global variables for game mode and current game instance.
game_mode = None  # e.g., "headsup"
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
    def __init__(self, num_decks=1):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = []
        for _ in range(num_decks):
            self.cards.extend([Card(s, r) for s in suits for r in ranks])
            # Ensure the 5 of Hearts is included.
            if not any(str(c) == "5 of Hearts" for c in self.cards):
                self.cards.append(Card("Hearts", "5"))
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self, num_cards):
        return [self.cards.pop(0) for _ in range(num_cards)]

# Ranking table and scoring constants.
RANK_PRIORITY = {
    "5 of Hearts": 200,
    "J of Hearts": 199,
    "A of Hearts": 198,
    "A_red": 197, "K_red": 196, "Q_red": 195,
    "10_red": 194, "9_red": 193, "8_red": 192, "7_red": 191,
    "6_red": 190, "4_red": 189, "3_red": 188, "2_red": 187,
    "2_black": 101, "3_black": 102, "4_black": 103, "6_black": 104,
    "7_black": 105, "8_black": 106, "9_black": 107, "10_black": 108,
    "Q_black": 110, "K_black": 111, "A_black": 112
}
HAND_TOTAL_POINTS = 30
BONUS_POINTS = 5

def get_card_rank(card_str, trump=None):
    if trump is not None and trump in ["Diamonds", "Clubs", "Spades"]:
        if trump == "Diamonds":
            trump_dict = {
                "5 of Diamonds": 200,
                "J of Diamonds": 199,
                "A of Hearts": 198,
                "A of Diamonds": 197,
                "K of Diamonds": 196,
                "Q of Diamonds": 195,
                "10 of Diamonds": 194,
                "9 of Diamonds": 193,
                "8 of Diamonds": 192,
                "7 of Diamonds": 191,
                "6 of Diamonds": 190,
                "4 of Diamonds": 189,
                "3 of Diamonds": 188,
                "2 of Diamonds": 187
            }
        elif trump == "Clubs":
            trump_dict = {
                "5 of Clubs": 200,
                "J of Clubs": 199,
                "A of Hearts": 198,
                "A of Clubs": 197,
                "K of Clubs": 196,
                "Q of Clubs": 195,
                "10 of Clubs": 194,
                "9 of Clubs": 193,
                "8 of Clubs": 192,
                "7 of Clubs": 191,
                "6 of Clubs": 190,
                "4 of Clubs": 189,
                "3 of Clubs": 188,
                "2 of Clubs": 187
            }
        elif trump == "Spades":
            trump_dict = {
                "5 of Spades": 200,
                "J of Spades": 199,
                "A of Hearts": 198,
                "A of Spades": 197,
                "K of Spades": 196,
                "Q of Spades": 195,
                "10 of Spades": 194,
                "9 of Spades": 193,
                "8 of Spades": 192,
                "7 of Spades": 191,
                "6 of Spades": 190,
                "4 of Spades": 189,
                "3 of Spades": 188,
                "2 of Spades": 187
            }
        if card_str in trump_dict:
            return trump_dict[card_str]
    if card_str in RANK_PRIORITY:
        return RANK_PRIORITY[card_str]
    rank, suit = card_str.split(" of ")
    if suit in ["Hearts", "Diamonds"]:
        return RANK_PRIORITY.get(f"{rank}_red", 50)
    else:
        return RANK_PRIORITY.get(f"{rank}_black", 50)

# Image URL functions.
def getCardImageUrl(card):
    parts = card.split(" of ")
    if len(parts) != 2:
        return ""
    rank, suit = parts
    rank_code = "0" if rank == "10" else (rank if rank in ["J","Q","K","A"] else rank)
    suit_code = suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

def getCardBackUrl():
    return "https://deckofcardsapi.com/static/img/back.png"

# Extended Player class.
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []  # Collected cards from won tricks.
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def trump_count(self, trump):
        return sum(1 for card in self.hand if card.suit == trump)
    def discard_auto(self, trump):
        before = len(self.hand)
        trump_cards = [card for card in self.hand if card.suit == trump]
        self.hand = trump_cards
        return before - len(self.hand)  # Number of cards discarded.

# Extended Game class (Heads Up variant only).
class Game:
    def __init__(self, mode):
        self.mode = mode  # Only "headsup" implemented.
        self.players = self.initialize_players(mode)
        self.num_players = len(self.players)
        self.deck = Deck(num_decks=1)
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # 0 = human, 1 = computer.
        self.bid = 0            # Winning bid value.
        self.leading_player = None
        self.trick_count = 0
        self.trick_log_text = ""
        self.current_lead_suit = None
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trick_history = []  # List of trick objects.
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
        # Clear trump display.
        self.trump_suit = None
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_phase(self, bidder_index, discards):
        # Manual discard: remove each card in discards from bidder's hand.
        bidder = self.players[bidder_index]
        initial = len(bidder.hand)
        bidder.hand = [card for card in bidder.hand if str(card) not in discards]
        discarded_count = initial - len(bidder.hand)
        return {"player_hand": [str(c) for c in self.players[0].hand],
                "discard_count": discarded_count}
    def attach_kitty(self, player_index, keep_list):
        bidder = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    bidder.hand.append(c)
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": [str(c) for c in self.players[0].hand]}
    def play_trick(self, played_card=None):
        # Trick play in Heads Up.
        played = {}
        if self.leading_player == 1:
            # Computer leads.
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
                if played_card not in [str(c) for c in self.players[0].hand]:
                    return {"trick_result": "Invalid card.", "current_trick_cards": {}}, None
                human_card = next(c for c in self.players[0].hand if str(c) == played_card)
                self.players[0].hand.remove(human_card)
                played[0] = human_card
                self.trick_log_text = f"You played {human_card}."
            # Create an object mapping each player's name to their played card.
            current_trick_cards = {
                self.players[1].name: str(played.get(1)) if played.get(1) else "",
                self.players[0].name: str(played.get(0)) if played.get(0) else ""
            }
            comp_card = played.get(1)
            human_card = played.get(0)
            # Determine winner.
            if human_card and human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
                winner = "You"
            else:
                r_human = get_card_rank(str(human_card), trump=self.trump_suit) if human_card else -1
                r_comp = get_card_rank(str(comp_card), trump=self.trump_suit) if comp_card else -1
                winner = "You" if r_human > r_comp else "Computer"
            self.players[0 if winner=="You" else 1].score += 5
            self.players[0 if winner=="You" else 1].tricks_won += 1
            # Record trick history.
            trick_info = {
                "trick_number": self.trick_count + 1,
                "cards": current_trick_cards,
                "winner": winner
            }
            self.trick_history.append(trick_info)
            self.leading_player = 0 if winner=="You" else 1
        else:
            # Human leads.
            if played_card is None:
                return {"trick_result": "Your turn to lead.", "current_trick_cards": {}}, None
            if played_card not in [str(c) for c in self.players[0].hand]:
                return {"trick_result": "Invalid card.", "current_trick_cards": {}}, None
            human_card = next(c for c in self.players[0].hand if str(c) == played_card)
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
            current_trick_cards = {
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
            trick_info = {
                "trick_number": self.trick_count + 1,
                "cards": current_trick_cards,
                "winner": winner
            }
            self.trick_history.append(trick_info)
            self.leading_player = 0 if winner=="You" else 1
        self.trick_count += 1

        # If hand is complete, return summary.
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
            return {"trick_result": result_text, "current_trick_cards": current_trick_cards, "trick_history": self.trick_history}, hand_scores
        else:
            # Return current trick info along with who won this trick.
            return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick_cards, "trick_winner": winner}, None

#################################
#           ROUTES              #
#################################

# Landing page: Game mode selection.
@app.route("/", methods=["GET"])
def landing():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Card Game - Select Mode</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; }
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
          if (response.ok) {
            window.location.href = '/game';
          } else {
            document.body.innerHTML += "<p>Error setting game mode.</p>";
          }
        }
      </script>
    </body>
    </html>
    """)

# Main game UI.
@app.route("/game", methods=["GET"])
def game_ui():
    # Clear trump display and trick history when starting a new hand.
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Card Game</title>
      <link rel="icon" href="https://deckofcardsapi.com/static/img/5_of_clubs.png" type="image/png">
      <style>
        body { font-family: Arial, sans-serif; background-color: #35654d; color: #fff; margin: 0; padding: 0; }
        #gameContainer { max-width: 1000px; margin: 20px auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }
        .card-row { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .card-image { width: 70px; height: auto; cursor: pointer; border: 2px solid transparent; border-radius: 8px; }
        .selected-card { border-color: #f1c40f; }
        button { margin: 10px; padding: 10px 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; }
        .section { margin: 20px 0; display: none; }
        #scoreBoard { font-weight: bold; margin-bottom: 10px; font-size: 20px; }
        #trumpDisplay { margin-bottom: 10px; }
        #trumpDisplay span { font-size: 48px; }
        #bidButtons button { background-color: #f39c12; color: #fff; }
        #bidButtons button:disabled { background-color: #999; }
        #trickSection { border-top: 2px solid #fff; padding-top: 20px; }
        #trickPiles { display: flex; justify-content: space-around; margin-top: 20px; }
        .pile { width: 45%; background-color: #3b7d63; padding: 10px; border-radius: 5px; }
        #discardMessage { font-size: 18px; margin-bottom: 10px; }
        #discardCount { font-size: 18px; margin-top: 5px; }
        #bidError { color: #ffcccc; }
      </style>
    </head>
    <body>
      <div id="gameContainer">
        <h1>45's Card Game</h1>
        <div id="scoreBoard">Player: 0 | Computer: 0</div>
        <div id="trumpDisplay"></div>
        <div>
          <h2>Dealer: <span id="dealer"></span></h2>
          <button id="dealCardsButton">Deal Cards</button>
        </div>
        <div id="playerHandSection" class="section">
          <h2>Your Hand</h2>
          <div id="playerHand" class="card-row"></div>
        </div>
        <div id="biddingSection" class="section">
          <h2>Bidding</h2>
          <p id="computerBid"></p>
          <div id="bidButtons">
            <button class="bidButton" data-bid="0">Pass</button>
            <button class="bidButton" data-bid="15">15</button>
            <button class="bidButton" data-bid="20">20</button>
            <button class="bidButton" data-bid="25">25</button>
            <button class="bidButton" data-bid="30">30</button>
          </div>
          <p id="bidError"></p>
        </div>
        <div id="trumpSelectionSection" class="section">
          <h2>Select Trump Suit</h2>
          <div style="display: flex; justify-content: center; gap: 20px;">
            <button class="trumpButton" data-suit="Hearts" style="background-color:#e74c3c;">♥</button>
            <button class="trumpButton" data-suit="Diamonds" style="background-color:#f1c40f;">♦</button>
            <button class="trumpButton" data-suit="Clubs" style="background-color:#27ae60;">♣</button>
            <button class="trumpButton" data-suit="Spades" style="background-color:#2980b9;">♠</button>
          </div>
        </div>
        <div id="kittySection" class="section">
          <h2>Kitty Cards</h2>
          <p id="kittyPrompt">Click "Reveal Kitty" to see the kitty.</p>
          <div id="kittyCards" class="card-row"></div>
          <button id="revealKittyButton">Reveal Kitty</button>
          <button id="submitKittyButton" style="display:none;">Submit Kitty Selection</button>
        </div>
        <div id="discardSection" class="section">
          <h2>Discard Phase</h2>
          <p id="discardMessage">Select cards to discard (0-4):</p>
          <div id="discardHand" class="card-row"></div>
          <p id="discardCount">Discarding 0 card(s)</p>
          <button id="skipDiscardButton">Submit Discards</button>
          <p id="computerDiscardInfo"></p>
        </div>
        <div id="trickSection" class="section">
          <h2>Trick Phase</h2>
          <div id="currentTrick" class="card-row"></div>
          <p id="playPrompt"></p>
          <button id="playTrickButton">Play Selected Card</button>
        </div>
        <div id="trickPiles">
          <div id="dealerTrickPile" class="pile">
            <h3>Dealer's Tricks</h3>
          </div>
          <div id="playerTrickPile" class="pile">
            <h3>Your Tricks</h3>
          </div>
        </div>
      </div>
      <footer>&copy; O'Donohue Software</footer>
      <script>
        let computerLeads = false;
        let currentScore = { player: 0, computer: 0 };

        function updateScoreBoard(p, c) {
          currentScore.player = p;
          currentScore.computer = c;
          document.getElementById("scoreBoard").innerText = `Player: ${p} | Computer: ${c}`;
        }

        async function sendRequest(url, data = {}) {
          try {
            const response = await fetch(url, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(data)
            });
            if (!response.ok) {
              const errData = await response.json();
              return { error: errData.error || "Error" };
            }
            return await response.json();
          } catch (error) {
            console.error("Network error:", error);
            return { error: error.message };
          }
        }

        function getCardImageUrl(card) {
          const parts = card.split(" of ");
          if (parts.length !== 2) return "";
          let [rank, suit] = parts;
          const rank_code = rank === "10" ? "0" : (["J","Q","K","A"].includes(rank) ? rank : rank);
          const suit_code = suit[0].toUpperCase();
          return `https://deckofcardsapi.com/static/img/${rank_code}${suit_code}.png`;
        }

        function getCardBackUrl() {
          return "https://deckofcardsapi.com/static/img/back.png";
        }

        function renderHand(containerId, hand, selectable=false) {
          const container = document.getElementById(containerId);
          container.innerHTML = "";
          hand.forEach(card => {
            const img = document.createElement("img");
            img.src = getCardImageUrl(card);
            img.alt = card;
            img.className = "card-image";
            if (selectable) {
              img.addEventListener("click", () => {
                // For discard area, allow multiple selections (do not deselect others).
                img.classList.toggle("selected-card");
                if (containerId === "discardHand") updateDiscardCount();
              });
            }
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

        function updateDiscardCount() {
          const count = document.querySelectorAll("#discardHand .selected-card").length;
          document.getElementById("discardCount").innerText = "Discarding " + count + " card(s)";
        }

        async function startTrickIfComputerLeads() {
          const leadResp = await sendRequest("/play_trick", { played_card: null });
          if (leadResp && !leadResp.error) {
            if (leadResp.computer_card) {
              document.getElementById("currentTrick").innerHTML = "";
              // Display computer's played card on the right.
              const compDiv = document.createElement("div");
              compDiv.style.display = "inline-block";
              compDiv.style.margin = "10px";
              compDiv.innerHTML = `<h4>Computer</h4><img src="${getCardImageUrl(leadResp.computer_card)}" alt="${leadResp.computer_card}" class="card-image">`;
              document.getElementById("currentTrick").appendChild(compDiv);
              document.getElementById("playPrompt").innerText = "Computer has led. Your turn to play.";
            } else {
              document.getElementById("trickResult").innerText = leadResp.trick_result;
            }
          } else if (leadResp.error) {
            document.getElementById("trickResult").innerText = leadResp.error;
          }
        }

        // --- Event Handlers ---

        // 1. Deal Cards.
        document.getElementById("dealCardsButton").addEventListener("click", async () => {
          const result = await sendRequest("/deal_cards");
          if (result.error) {
            alert(result.error);
            return;
          }
          // Clear trump display and trick piles for a new hand.
          document.getElementById("trumpDisplay").innerHTML = "";
          document.getElementById("dealerTrickPile").innerHTML = "<h3>Dealer's Tricks</h3>";
          document.getElementById("playerTrickPile").innerHTML = "<h3>Your Tricks</h3>";
          document.getElementById("scoreBoard").innerText = "Player: 0 | Computer: 0";
          document.getElementById("trickResult").innerText = "";
          document.getElementById("currentTrick").innerHTML = "";
          document.getElementById("playPrompt").innerText = "";
          document.getElementById("discardCount").innerText = "Discarding 0 card(s)";
          // Clear any previous bid error.
          document.getElementById("bidError").innerText = "";
          // Clear kitty prompt.
          document.getElementById("kittyPrompt").innerText = "Click 'Reveal Kitty' to see the kitty.";
          document.getElementById("revealKittyButton").style.display = "inline-block";
          document.getElementById("submitKittyButton").style.display = "none";
          document.getElementById("dealer").innerText = result.dealer;
          renderHand("playerHand", result.player_hand, true);
          showSection("playerHandSection");
          // If human is dealer, get computer bid.
          if (result.dealer === "You") {
            const compBidResp = await sendRequest("/computer_first_bid");
            if (compBidResp && !compBidResp.error) {
              document.getElementById("computerBid").innerText = `Computer's bid: ${compBidResp.computer_bid}`;
              if (parseInt(compBidResp.computer_bid) === 15) {
                document.querySelectorAll(".bidButton").forEach(btn => {
                  const bidVal = parseInt(btn.dataset.bid);
                  btn.disabled = (bidVal !== 0 && bidVal !== 20);
                });
              } else if (parseInt(compBidResp.computer_bid) === 20) {
                document.querySelectorAll(".bidButton").forEach(btn => {
                  const bidVal = parseInt(btn.dataset.bid);
                  btn.disabled = (bidVal !== 0 && bidVal !== 25);
                });
              } else if (parseInt(compBidResp.computer_bid) === 25) {
                document.querySelectorAll(".bidButton").forEach(btn => {
                  const bidVal = parseInt(btn.dataset.bid);
                  btn.disabled = (bidVal !== 0 && bidVal !== 30);
                });
              }
            }
          }
          showSection("biddingSection");
        });

        // 2. Bidding.
        document.querySelectorAll(".bidButton").forEach(btn => {
          btn.addEventListener("click", async () => {
            btn.classList.add("selected-card");
            const bidValue = parseInt(btn.dataset.bid);
            const compBidText = document.getElementById("computerBid").innerText;
            const compBid = compBidText ? parseInt(compBidText.replace("Computer's bid: ", "")) : 0;
            const result = await sendRequest("/submit_bid", { player_bid: bidValue, computer_bid: compBid });
            if (result.error) {
              document.getElementById("bidError").innerText = result.error;
              return;
            }
            document.getElementById("computerBid").innerText = `Computer's bid: ${result.computer_bid}`;
            hideSection("biddingSection");
            if (result.bid_winner === "Player") {
              showSection("trumpSelectionSection");
            } else {
              updateTrumpDisplay(result.trump_suit);
              computerLeads = true;
              // For computer bidder, automatically perform discard.
              const discResp = await sendRequest("/discard_and_draw", {});
              if (discResp.error) {
                document.getElementById("bidError").innerText = discResp.error;
              } else {
                document.getElementById("computerDiscardInfo").innerText = "Computer discarded " + discResp.computer_discard_count + " card(s).";
              }
              showSection("trickSection");
              if (computerLeads) startTrickIfComputerLeads();
            }
          });
        });

        // 3. Trump Selection.
        document.querySelectorAll(".trumpButton").forEach(btn => {
          btn.addEventListener("click", async () => {
            const suit = btn.dataset.suit;
            const resp = await sendRequest("/select_trump", { trump_suit: suit });
            if (resp.error) {
              document.getElementById("bidError").innerText = resp.error;
              return;
            }
            updateTrumpDisplay(suit);
            hideSection("trumpSelectionSection");
            renderKittyCards("kittyCards", resp.kitty_cards);
            showSection("kittySection");
          });
        });

        // 4. Kitty Selection.
        document.getElementById("revealKittyButton").addEventListener("click", () => {
            // Flip kitty cards.
            const kittyImgs = document.getElementById("kittyCards").querySelectorAll("img");
            kittyImgs.forEach(img => {
              img.src = getCardImageUrl(img.alt);
            });
            document.getElementById("kittyPrompt").innerText = "Select the kitty cards you want to add, then click 'Submit Kitty Selection'.";
            document.getElementById("revealKittyButton").style.display = "none";
            document.getElementById("submitKittyButton").style.display = "inline-block";
        });

        document.getElementById("submitKittyButton").addEventListener("click", async () => {
            const selected = [...document.querySelectorAll("#kittyCards .selected-card")].map(img => img.alt);
            const resp = await sendRequest("/attach_kitty", { keep_cards: selected });
            if (resp.error) {
              document.getElementById("bidError").innerText = resp.error;
              return;
            }
            renderHand("playerHand", resp.player_hand, true);
            hideSection("kittySection");
            // Now allow manual discard selection.
            renderHand("discardHand", resp.player_hand, true);
            document.getElementById("discardMessage").innerText = "Select cards to discard (0-4):";
            updateDiscardCount();
            showSection("discardSection");
        });

        // 4b. Discard Phase – Submit Discards.
        document.getElementById("skipDiscardButton").addEventListener("click", async () => {
            const selected = [...document.querySelectorAll("#discardHand .selected-card")].map(img => img.alt);
            const resp = await sendRequest("/discard_and_draw", { discarded_cards: selected });
            if (resp.error) {
              document.getElementById("bidError").innerText = resp.error;
              return;
            }
            renderHand("playerHand", resp.player_hand, true);
            hideSection("discardSection");
            showSection("trickSection");
            if (computerLeads) startTrickIfComputerLeads();
        });

        // 5. Trick Phase – Play a card.
        document.getElementById("playTrickButton").addEventListener("click", async () => {
            const selected = document.querySelector("#playerHand .selected-card");
            let cardStr = selected ? selected.alt : null;
            const resp = await sendRequest("/play_trick", { played_card: cardStr });
            if (resp.error) {
              document.getElementById("trickResult").innerText = resp.error;
              return;
            }
            // Display current trick as images with a slight delay.
            if (resp.current_trick_cards) {
              const container = document.getElementById("currentTrick");
              container.innerHTML = "";
              // Create a temporary display for 1.5 seconds.
              for (let key in resp.current_trick_cards) {
                const div = document.createElement("div");
                div.style.display = "inline-block";
                div.style.margin = "10px";
                div.innerHTML = `<h4>${key}</h4><img src="${getCardImageUrl(resp.current_trick_cards[key])}" alt="${resp.current_trick_cards[key]}" class="card-image">`;
                container.appendChild(div);
              }
              setTimeout(() => {
                // After delay, move these cards into the collected trick pile.
                if (resp.trick_winner) {
                  addTrickToPile(Object.values(resp.current_trick_cards), resp.trick_winner);
                }
                container.innerHTML = "";
              }, 1500);
            }
            document.getElementById("trickResult").innerText = resp.trick_result;
            renderHand("playerHand", resp.player_hand, true);
            updateScoreBoard(resp.player_score, Object.values(resp.computer_score).join(" | "));
            if (resp.hand_scores) {
              alert("Hand Scores: " + JSON.stringify(resp.hand_scores));
            }
        });
      </script>
    </body>
    </html>
    """)

#################################
#           API ROUTES          #
#################################

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global game_mode, current_game
    data = request.json
    mode = data.get("mode", "headsup")
    game_mode = mode
    current_game = Game(mode)
    return jsonify({"mode": mode})

@app.route("/deal_cards", methods=["POST"])
def deal_cards_route():
    global current_game
    if current_game is None:
        return jsonify({"error": "Game mode not set. Please select a game mode."}), 400
    current_game.deal_hands()
    current_game.starting_scores = {p.name: p.score for p in current_game.players}
    # Clear trump and trick history when a new hand is dealt.
    current_game.trump_suit = None
    current_game.trick_history = []
    dealer = current_game.players[0].name  # For Heads Up, human is dealer.
    return jsonify({"player_hand": [str(c) for c in current_game.players[0].hand],
                    "dealer": dealer, "mode": game_mode})

@app.route("/computer_first_bid", methods=["POST"])
def computer_first_bid():
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def submit_bid():
    try:
        if current_game is None:
            return jsonify({"error": "No game in progress. Set a game mode and deal cards first."}), 400
        data = request.json
        player_bid = data.get("player_bid", None)
        comp_bid = data.get("computer_bid", None)
        if comp_bid is None:
            return jsonify({"error": "Computer bid missing."}), 400
        # If computer bids 30, bidding stops.
        if comp_bid == 30:
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            current_game.bid_winner = 1
            current_game.bid = comp_bid
            current_game.leading_player = 1
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer", "trump_suit": trump_suit, "kitty_cards": kitty})
        # If computer passes (bid 0), dealer must bid 15.
        if comp_bid == 0:
            if player_bid != 15:
                return jsonify({"error": "Invalid bid. When opponent passes, you must bid 15."}), 400
            else:
                current_game.bid_winner = 0
                current_game.bid = 15
                current_game.leading_player = 0
                return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})
        # Otherwise, if computer bid is 15, 20, or 25, the only valid dealer bid is comp_bid+5 or pass (0).
        let_bid = comp_bid + 5
        if player_bid == 0:
            current_game.bid_winner = 1
            current_game.bid = comp_bid
            current_game.leading_player = 1
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer", "trump_suit": trump_suit, "kitty_cards": kitty})
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
def select_trump_route():
    data = request.json
    suit = data.get("trump_suit", "Hearts")
    kitty = current_game.confirm_trump(suit)
    return jsonify({"kitty_cards": kitty, "trump_suit": suit})

@app.route("/discard_and_draw", methods=["POST"])
def discard_and_draw():
    data = request.json
    discards = data.get("discarded_cards", None)
    result = current_game.discard_phase(current_game.bid_winner, discards)
    # For computer bidder, include discard count.
    if current_game.bid_winner == 1:
        comp_disc = current_game.players[1].discard_auto(current_game.trump_suit)
        result["computer_discard_count"] = comp_disc
    return jsonify(result)

@app.route("/attach_kitty", methods=["POST"])
def attach_kitty_route():
    data = request.json
    keep_cards = data.get("keep_cards", [])
    bidder = current_game.players[current_game.bid_winner]
    for card_str in keep_cards:
        for c in current_game.kitty:
            if str(c) == card_str:
                bidder.hand.append(c)
    current_game.kitty = [c for c in current_game.kitty if str(c) not in keep_cards]
    return jsonify({"player_hand": [str(c) for c in current_game.players[0].hand]})

@app.route("/play_trick", methods=["POST"])
def play_trick_route():
    data = request.json
    played_card = data.get("played_card")
    result_obj, hand_scores = current_game.play_trick(played_card)
    resp = {
        "trick_result": result_obj.get("trick_result", ""),
        "current_trick_cards": result_obj.get("current_trick_cards", {}),
        "trick_winner": result_obj.get("trick_winner", ""),
        "player_hand": [str(c) for c in current_game.players[0].hand],
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
