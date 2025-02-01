import os
from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
import random

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# Global variables for game mode and current game instance.
game_mode = None  # e.g., "headsup", "cutthroat", "partners", "5way"
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

# Ranking and scoring constants.
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
HAND_TOTAL_POINTS = 30   # Total points per hand (from tricks)
BONUS_POINTS = 5         # Bonus for highest card in the hand

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

# --- Image URL functions using Deck of Cards API ---
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

# --- Extended Player class ---
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []  # Collected cards from tricks
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def trump_count(self, trump):
        return sum(1 for card in self.hand if card.suit == trump)
    def discard_auto(self, trump):
        # Automatically discard non-trump cards.
        trump_cards = [card for card in self.hand if card.suit == trump]
        self.hand = trump_cards
        if len(self.hand) > 5:
            self.hand.sort(key=lambda card: get_card_rank(str(card), trump), reverse=True)
            self.hand = self.hand[:5]

# --- Extended Game class ---
class Game:
    def __init__(self, mode):
        self.mode = mode  # For now, only "headsup" is fully implemented.
        self.players = self.initialize_players(mode)
        self.num_players = len(self.players)
        self.deck = Deck(num_decks=1)
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # 0 for human, 1 for computer (in Heads Up)
        self.bid = 0            # Winning bid value
        self.leading_player = None
        self.trick_count = 0
        self.played_cards_log = []  # List of tuples: (card, player_index) for current trick
        self.trick_log_text = ""
        self.current_lead_suit = None
        self.starting_scores = {p.name: p.score for p in self.players}
    def initialize_players(self, mode):
        if mode == "headsup":
            return [Player("You"), Player("Computer")]
        # (Additional modes can be added here.)
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
        self.played_cards_log = []
        self.starting_scores = {p.name: p.score for p in self.players}
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_phase(self, bidder_index):
        bidder = self.players[bidder_index]
        bidder.discard_auto(self.trump_suit)
        return {"player_hand": [str(c) for c in self.players[0].hand]}
    def attach_kitty(self, player_index, keep_list):
        bidder = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    bidder.hand.append(c)
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": [str(c) for c in self.players[0].hand]}
    def play_trick(self, played_card=None):
        # Heads Up variant
        played = {}
        # If computer is leading:
        if self.leading_player == 1:
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
                    return {"trick_result": "Invalid card.", "current_trick_cards": []}, None
                human_card = next(c for c in self.players[0].hand if str(c)==played_card)
                self.players[0].hand.remove(human_card)
                played[0] = human_card
                self.trick_log_text = f"You played {human_card}."
            current_trick_cards = [str(card) for card in played.values()]
            comp_card = played.get(1)
            human_card = played.get(0)
            if human_card and human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
                winner = 0
            else:
                r_human = get_card_rank(str(human_card), trump=self.trump_suit) if human_card else -1
                r_comp = get_card_rank(str(comp_card), trump=self.trump_suit) if comp_card else -1
                winner = 0 if r_human > r_comp else 1
            self.players[winner].score += 5
            self.players[winner].tricks_won += 1
            self.players[winner].trick_pile.extend(current_trick_cards)
            self.leading_player = winner
        else:
            # Human leads.
            if played_card is None:
                return {"trick_result": "Your turn to lead.", "current_trick_cards": []}, None
            if played_card not in [str(c) for c in self.players[0].hand]:
                return {"trick_result": "Invalid card.", "current_trick_cards": []}, None
            human_card = next(c for c in self.players[0].hand if str(c)==played_card)
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
            current_trick_cards = [str(card) for card in played.values()]
            if human_card.suit == self.trump_suit and (not comp_card or comp_card.suit != self.trump_suit):
                winner = 0
            else:
                r_human = get_card_rank(str(human_card), trump=self.trump_suit) if human_card else -1
                r_comp = get_card_rank(str(comp_card), trump=self.trump_suit) if comp_card else -1
                winner = 0 if r_human > r_comp else 1
            self.players[winner].score += 5
            self.players[winner].tricks_won += 1
            self.players[winner].trick_pile.extend(current_trick_cards)
            self.leading_player = winner
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
                for p in self.players:
                    if p.name == best_player:
                        p.score += BONUS_POINTS
                        bonus_text = f" Highest card was {best_card}. Bonus {BONUS_POINTS} points to {best_player}."
                        break
            result_text = self.trick_log_text + bonus_text
            hand_scores = {p.name: p.score - self.starting_scores[p.name] for p in self.players}
            bidder = self.bid_winner
            if hand_scores[self.players[bidder].name] < self.bid:
                hand_scores[self.players[bidder].name] = -self.bid
                hand_scores[self.players[1-bidder].name] = HAND_TOTAL_POINTS - (-self.bid)
                result_text += f" Bid not met. {self.players[bidder].name} loses {self.bid} points."
            return {"trick_result": result_text, "current_trick_cards": current_trick_cards}, hand_scores
        else:
            return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick_cards}, None

#################################
#           ROUTES              #
#################################

# Root route: Mode selection landing page.
@app.route("/", methods=["GET"])
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>45's Card Game - Select Game Mode</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; }
        .mode-btn { padding: 10px 20px; margin: 10px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer; }
      </style>
    </head>
    <body>
      <h1>Welcome to 45's Card Game</h1>
      <p>Select Game Mode:</p>
      <button class="mode-btn" onclick="setMode('headsup')">Heads Up</button>
      <button class="mode-btn" onclick="setMode('cutthroat')">Cut Throat</button>
      <button class="mode-btn" onclick="setMode('partners')">Partners</button>
      <button class="mode-btn" onclick="setMode('5way')">5 Way Cutthroat</button>
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
            alert('Error setting game mode.');
          }
        }
      </script>
    </body>
    </html>
    """)

# Main game UI.
@app.route("/game", methods=["GET"])
def game_ui():
    # This template contains the game UI (bidding, dealing, kitty, discard, trick play, etc.)
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>45's Card Game</title>
  <link rel="icon" href="https://deckofcardsapi.com/static/img/5_of_clubs.png" type="image/png">
  <style>
    body { font-family: Arial, sans-serif; text-align: center; background-color: #35654d; color: #fff; margin: 0; padding: 0; }
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
    #bidButtons button:hover { background-color: #e67e22; }
    #trickSection { border-top: 2px solid #fff; padding-top: 20px; }
    #trickPiles { display: flex; justify-content: space-between; margin-top: 20px; }
    #dealerTrickPile, #playerTrickPile { width: 45%; background-color: #3b7d63; padding: 10px; border-radius: 5px; }
    #discardMessage { font-size: 18px; margin-bottom: 10px; }
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
    </div>
    <div id="trumpSelectionSection" class="section">
      <h2>Select Trump Suit</h2>
      <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <button class="trumpButton" data-suit="Hearts" style="background-color:#e74c3c;">Hearts</button>
        <button class="trumpButton" data-suit="Diamonds" style="background-color:#f1c40f;">Diamonds</button>
        <button class="trumpButton" data-suit="Clubs" style="background-color:#27ae60;">Clubs</button>
        <button class="trumpButton" data-suit="Spades" style="background-color:#2980b9;">Spades</button>
      </div>
    </div>
    <div id="kittySection" class="section">
      <h2>Kitty Cards</h2>
      <p>The kitty has been dealt.</p>
      <div id="kittyCards" class="card-row"></div>
      <button id="submitKittyButton">Reveal & Select Kitty Cards</button>
    </div>
    <div id="discardSection" class="section">
      <h2>Discard Phase</h2>
      <p id="discardMessage"></p>
      <div id="discardHand" class="card-row"></div>
      <button id="discardButton">Discard Selected Cards</button>
      <button id="skipDiscardButton">Skip Discard</button>
    </div>
    <div id="trickSection" class="section">
      <h2>Trick Phase</h2>
      <p id="trickResult"></p>
      <div id="currentTrick" class="card-row"></div>
      <p id="playPrompt"></p>
      <button id="playTrickButton">Play Selected Card</button>
    </div>
    <div id="trickPiles">
      <div id="dealerTrickPile">
        <h3>Dealer's Collected Tricks</h3>
      </div>
      <div id="playerTrickPile">
        <h3>Your Collected Tricks</h3>
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
      document.getElementById("scoreBoard").textContent = `Player: ${p} | Computer: ${c}`;
    }

    async function sendRequest(url, data = {}) {
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });
        if (!response.ok) {
          console.error(`Error: ${response.status} ${response.statusText}`);
          alert(`Request to ${url} failed: ${response.status} ${response.statusText}`);
          return null;
        }
        return await response.json();
      } catch (error) {
        console.error("Network error:", error);
        alert(`Network error: ${error.message}`);
        return null;
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
            if (containerId === "playerHand") {
              [...container.querySelectorAll(".selected-card")].forEach(i => {
                if(i !== img) i.classList.remove("selected-card");
              });
            }
            img.classList.toggle("selected-card");
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
          [...container.querySelectorAll(".selected-card")].forEach(i => {
            if(i !== img) i.classList.remove("selected-card");
          });
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
      const trumpDiv = document.getElementById("trumpDisplay");
      trumpDiv.innerHTML = `<span>Trump: <span style="font-size:48px;">${suitSymbols[suit]}</span></span>`;
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
      document.getElementById("currentTrick").innerHTML = "";
    }

    async function startTrickIfComputerLeads() {
      const leadResp = await sendRequest("/play_trick", { played_card: null });
      if (leadResp) {
        if (leadResp.computer_card) {
          document.getElementById("currentTrick").innerHTML = "";
          renderHand("currentTrick", [leadResp.computer_card], false);
          document.getElementById("trickResult").textContent = "";
          document.getElementById("playPrompt").textContent = "Computer has led. Please select a card from your hand.";
        } else {
          document.getElementById("trickResult").textContent = leadResp.trick_result;
        }
      }
    }

    // --- Event Handlers ---
    // 1. Deal Cards
    document.getElementById("dealCardsButton").addEventListener("click", async () => {
      const result = await sendRequest("/deal_cards");
      if (!result) return;
      document.getElementById("dealer").textContent = result.dealer;
      renderHand("playerHand", result.player_hand, true);
      showSection("playerHandSection");
      // If human is dealer, computer bids first.
      if (result.dealer === "You") {
        const compBidResp = await sendRequest("/computer_first_bid");
        if (compBidResp) {
          document.getElementById("computerBid").textContent = `Computer's bid: ${compBidResp.computer_bid}`;
          if (parseInt(compBidResp.computer_bid) === 20) {  // Example: if computer bid 20, human must bid 25 to win.
            // Disable all bid buttons except "Pass" and the required bid.
            document.querySelectorAll(".bidButton").forEach(btn => {
              const bidVal = parseInt(btn.dataset.bid);
              btn.disabled = (bidVal !== 0 && bidVal !== 25);
            });
          }
        }
      }
      showSection("biddingSection");
    });

    // 2. Bidding with Buttons
    document.querySelectorAll(".bidButton").forEach(btn => {
      btn.addEventListener("click", async () => {
        btn.classList.add("selected-card"); // Simple visual feedback.
        const bidValue = parseInt(btn.dataset.bid);
        const compBidText = document.getElementById("computerBid").textContent;
        const compBid = compBidText ? parseInt(compBidText.replace("Computer's bid: ", "")) : 0;
        const result = await sendRequest("/submit_bid", { player_bid: bidValue, computer_bid: compBid });
        if (!result) return;
        document.getElementById("computerBid").textContent = `Computer's bid: ${result.computer_bid}`;
        hideSection("biddingSection");
        if (result.bid_winner === "Player") {
          // Human wins bid → show trump selection.
          showSection("trumpSelectionSection");
        } else {
          updateTrumpDisplay(result.trump_suit);
          // Computer wins bid → automatically proceed to discard phase.
          computerLeads = true;
          renderHand("discardHand", [...document.getElementById("playerHand").querySelectorAll("img")].map(img => img.alt), true);
          let excess = document.getElementById("playerHand").querySelectorAll("img").length - 5;
          document.getElementById("discardMessage").textContent = "Please discard exactly " + excess + " card(s).";
          showSection("discardSection");
        }
      });
    });

    // 3. Trump Selection UI
    document.querySelectorAll(".trumpButton").forEach(btn => {
      btn.addEventListener("click", async () => {
        const suit = btn.dataset.suit;
        const resp = await sendRequest("/select_trump", { trump_suit: suit });
        if (!resp) return;
        updateTrumpDisplay(suit);
        hideSection("trumpSelectionSection");
        renderKittyCards("kittyCards", resp.kitty_cards);
        showSection("kittySection");
      });
    });

    // 4. Submit Kitty Selection – Reveal kitty cards and merge into hand.
    document.getElementById("submitKittyButton").addEventListener("click", async () => {
      const kittyImgs = document.getElementById("kittyCards").querySelectorAll("img");
      kittyImgs.forEach(img => {
        let cardVal = img.alt;
        img.src = getCardImageUrl(cardVal);
      });
      const selected = [...document.querySelectorAll("#kittyCards .selected-card")].map(img => img.alt);
      const resp = await sendRequest("/attach_kitty", { keep_cards: selected });
      if (!resp) return;
      renderHand("playerHand", resp.player_hand, true);
      hideSection("kittySection");
      // Automatically perform discard phase.
      const discardResp = await sendRequest("/discard_and_draw", {});
      if (discardResp.error) {
        alert(discardResp.error);
      }
      showSection("trickSection");
      if (computerLeads) {
        startTrickIfComputerLeads();
      }
    });

    // 4b. Skip Discard
    document.getElementById("skipDiscardButton").addEventListener("click", () => {
      hideSection("discardSection");
      showSection("trickSection");
      if (computerLeads) {
        startTrickIfComputerLeads();
      }
    });

    // 5. Trick Phase – Player plays a card.
    document.getElementById("playTrickButton").addEventListener("click", async () => {
      const selected = document.querySelector("#playerHand .selected-card");
      let cardStr = selected ? selected.alt : null;
      const resp = await sendRequest("/play_trick", { played_card: cardStr });
      if (!resp) return;
      if (resp.current_trick_cards) {
        renderHand("currentTrick", resp.current_trick_cards, false);
      }
      document.getElementById("trickResult").textContent = resp.trick_result;
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
    
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

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
            return jsonify({"error": "No game in progress. Please select a game mode and deal cards first."}), 400
        data = request.json
        player_bid = data.get("player_bid", 0)
        comp_bid = data.get("computer_bid", 0)
        let_bid = comp_bid + 5 if comp_bid > 0 else 0
        if player_bid != 0 and player_bid != let_bid:
            return jsonify({"error": f"Invalid bid. You must either pass (0) or bid {let_bid}."}), 400
        if comp_bid > player_bid:
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            current_game.bid_winner = 1
            current_game.bid = comp_bid
            current_game.leading_player = 1
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer", "trump_suit": trump_suit, "kitty_cards": kitty})
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
    result = current_game.discard_phase(current_game.bid_winner)
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
        "current_trick_cards": result_obj.get("current_trick_cards", []),
        "player_hand": [str(c) for c in current_game.players[0].hand],
        "player_score": current_game.players[0].score,
        "computer_score": {p.name: p.score for p in current_game.players if p.name != "You"}
    }
    if hand_scores:
        resp["hand_scores"] = hand_scores
    return jsonify(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
