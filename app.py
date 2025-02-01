from flask import Flask, request, jsonify, render_template_string, send_from_directory
import random, os

app = Flask(__name__)

############################
#        GAME LOGIC        #
############################

current_game = None
current_dealer = "Player"  # toggles each round

# Basic ranking table for non-trump (and trump Hearts)
RANK_PRIORITY = {
    "5 of Hearts": 200,
    "J of Hearts": 199,
    "A of Hearts": 198,
    # Red suits descending:
    "A_red": 197, "K_red": 196, "Q_red": 195,
    "10_red": 194, "9_red": 193, "8_red": 192, "7_red": 191,
    "6_red": 190, "4_red": 189, "3_red": 188, "2_red": 187,
    # Black suits ascending:
    "2_black": 101, "3_black": 102, "4_black": 103, "6_black": 104,
    "7_black": 105, "8_black": 106, "9_black": 107, "10_black": 108,
    "Q_black": 110, "K_black": 111, "A_black": 112
}

def get_card_rank(card_str, trump=None):
    """
    Returns a numeric rank for a card.
    If trump is one of Diamonds, Clubs, or Spades then a trump ranking dictionary is used:
      - Example: if trump is Spades:
            "5 of Spades": 200,
            "J of Spades": 199,
            "A of Hearts": 198, (treated as trump, third highest)
            then the remaining Spade cards follow.
    Otherwise, if trump is Hearts or not provided, fall back to RANK_PRIORITY.
    """
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

# --- Card Image Functions using Deck of Cards API ---
def getCardImageUrl(card):
    """
    Converts a card string (e.g., "J of Hearts") to the Deck of Cards API URL.
    For "10", use "0".
    """
    parts = card.split(" of ")
    if len(parts) != 2:
        return ""
    rank, suit = parts
    rank_code = "0" if rank == "10" else (rank if rank in ["J", "Q", "K", "A"] else rank)
    suit_code = suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

def getCardBackUrl():
    return "https://deckofcardsapi.com/static/img/back.png"

# --- Core Classes ---
class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(s, r) for s in suits for r in ranks]
        if not any(str(c) == "5 of Hearts" for c in self.cards):
            self.cards.append(Card("Hearts", "5"))
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self, num_cards):
        return [self.cards.pop(0) for _ in range(num_cards)]

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def discard_cards(self, discards):
        self.hand = [card for card in self.hand if str(card) not in discards]

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = [Player("You"), Player("Computer")]
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # 0 = player, 1 = computer
        self.leading_player = None  # Set to bid winner initially
        self.trick_count = 0
        self.played_cards_log = []  # List of tuples: (card, player_index)
        self.trick_log_text = ""
        self.current_lead_suit = None
        self.player_trick_pile = []  # Collected trick cards for player
        self.dealer_trick_pile = []  # Collected trick cards for dealer
    def deal_hands(self):
        self.deck.shuffle()
        self.kitty = self.deck.deal(3)
        for p in self.players:
            p.hand = []
            p.tricks_won = 0
        self.players[0].add_to_hand(self.deck.deal(5))
        self.players[1].add_to_hand(self.deck.deal(5))
        self.player_trick_pile = []
        self.dealer_trick_pile = []
        self.trick_log_text = ""
        self.trick_count = 0
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_and_draw(self, player_index, discards):
        p = self.players[player_index]
        excess = len(p.hand) - 5
        if len(discards) != excess:
            return {"error": f"Please discard exactly {excess} card(s)."}
        p.discard_cards(discards)
        # In this game, no extra cards are drawn; the final hand is exactly 5 cards.
        return {"player_hand": [str(c) for c in p.hand]}
    def attach_kitty(self, player_index, keep_list):
        p = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    p.hand.append(c)
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return {"player_hand": [str(c) for c in p.hand]}
    def play_trick(self, played_card=None):
        """
        Trick Phase with Follow Suit & Reneging.
          - If computer wins the bid (leading_player == 1), then the computer leads the first trick.
          - In the "player leads" branch, if the player's card is trump and the computer's card is not trump, then the player wins automatically.
          - All played cards are collected into a "current trick" array and then added to the appropriate trick pile.
          - Each trick win awards 5 points.
          - After 5 tricks or if the hand is empty, the highest card played in that hand receives a bonus of 5 points.
          - The running score continues across hands until one player reaches 120.
        """
        def is_renegable(card_str, trump):
            if card_str == f"5 of {trump}" or card_str == f"J of {trump}":
                return True
            if trump == "Hearts" and card_str == "A of Hearts":
                return True
            return False

        # --- Computer leads (when computer lost bid, it leads first) ---
        if self.leading_player == 1:
            if played_card is None:
                if len(self.players[1].hand) == 0:
                    return {"trick_result": "Computer has no card to lead.", "computer_card": None, "current_trick_cards": []}, None
                comp_card = self.players[1].hand.pop(0)
                self.current_lead_suit = comp_card.suit
                self.played_cards_log.append((comp_card, 1))
                self.trick_log_text += f"Computer leads with {comp_card}. "
                return {"trick_result": "", "computer_card": str(comp_card), "current_trick_cards": [str(comp_card)]}, None
            else:
                if played_card not in [str(c) for c in self.players[0].hand]:
                    return {"trick_result": "Invalid card."}, None
                player_card = next(c for c in self.players[0].hand if str(c)==played_card)
                # Enforce follow-suit if available
                if any(c.suit == self.current_lead_suit for c in self.players[0].hand):
                    if player_card.suit != self.current_lead_suit:
                        if not (player_card.suit == self.trump_suit and is_renegable(str(player_card), self.trump_suit)):
                            return {"trick_result": f"You must follow suit ({self.current_lead_suit})."}, None
                self.players[0].hand.remove(player_card)
                self.played_cards_log.append((player_card, 0))
                self.trick_log_text += f"You played {player_card}. "
                current_trick_cards = [str(card) for card, _ in self.played_cards_log]
                comp_card, _ = self.played_cards_log[0]
                # Compare normally
                rank_player = get_card_rank(str(player_card), trump=self.trump_suit)
                rank_comp = get_card_rank(str(comp_card), trump=self.trump_suit)
                winner = 0 if rank_player > rank_comp else 1
                if winner == 0:
                    self.trick_log_text += "You win the trick! "
                    self.player_trick_pile.extend(current_trick_cards)
                else:
                    self.trick_log_text += "Computer wins the trick! "
                    self.dealer_trick_pile.extend(current_trick_cards)
                self.players[winner].score += 5
                self.players[winner].tricks_won += 1
                self.leading_player = winner
                self.trick_count += 1
                self.played_cards_log = []
                self.current_lead_suit = None
                # End of hand: award bonus and check for game end.
                if self.trick_count >= 5 or len(self.players[0].hand) == 0:
                    best_card, best_player = self.get_highest_card()
                    self.players[best_player].score += 5  # Bonus is 5 points now.
                    self.trick_log_text += f"Round over! Highest card was {best_card}. Scores: You {self.players[0].score} | Computer {self.players[1].score}."
                    round_winner = "You" if self.players[0].score > self.players[1].score else "Computer"
                    return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick_cards}, round_winner
                return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick_cards}, None

        # --- Player leads ---
        else:
            if played_card is None:
                return {"trick_result": "Your turn to lead. Please select a card."}, None
            if played_card not in [str(c) for c in self.players[0].hand]:
                return {"trick_result": "Invalid card."}, None
            player_card = next(c for c in self.players[0].hand if str(c)==played_card)
            self.players[0].hand.remove(player_card)
            self.current_lead_suit = player_card.suit
            self.played_cards_log.append((player_card, 0))
            self.trick_log_text += f"You lead with {player_card}. "
            comp_hand = self.players[1].hand
            comp_follow = [c for c in comp_hand if c.suit == self.current_lead_suit]
            if comp_follow:
                comp_card = comp_follow[0]
                comp_hand.remove(comp_card)
            elif any(c.suit == self.trump_suit for c in comp_hand):
                for idx, card in enumerate(comp_hand):
                    if card.suit == self.trump_suit:
                        comp_card = comp_hand.pop(idx)
                        break
            else:
                comp_card = comp_hand.pop(0) if comp_hand else None
            if comp_card:
                self.played_cards_log.append((comp_card, 1))
                self.trick_log_text += f"Computer plays {comp_card}. "
            else:
                self.trick_log_text += "Computer has no card to play. "
            current_trick_cards = [str(card) for card, _ in self.played_cards_log]
            # --- NEW: If player's card is trump and computer's card is not trump, player wins automatically.
            if player_card.suit == self.trump_suit and (comp_card is None or comp_card.suit != self.trump_suit):
                winner = 0
            else:
                if comp_card:
                    rank_player = get_card_rank(str(player_card), trump=self.trump_suit)
                    rank_comp = get_card_rank(str(comp_card), trump=self.trump_suit)
                    winner = 0 if rank_player > rank_comp else 1
                else:
                    winner = 0
            self.players[winner].score += 5
            self.players[winner].tricks_won += 1
            self.leading_player = winner
            self.trick_count += 1
            if winner == 0:
                self.trick_log_text += "You win the trick! "
                self.player_trick_pile.extend(current_trick_cards)
            else:
                self.trick_log_text += "Computer wins the trick! "
                self.dealer_trick_pile.extend(current_trick_cards)
            self.played_cards_log = []
            self.current_lead_suit = None
            if self.trick_count >= 5 or len(self.players[0].hand)==0:
                best_card, best_player = self.get_highest_card()
                self.players[best_player].score += 5  # Bonus of 5 points.
                self.trick_log_text += f"Round over! Highest card was {best_card}. Scores: You {self.players[0].score} | Computer {self.players[1].score}."
                round_winner = "You" if self.players[0].score > self.players[1].score else "Computer"
                return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick_cards}, round_winner
            return {"trick_result": self.trick_log_text, "current_trick_cards": current_trick_cards}, None

    def get_highest_card(self):
        best_card, best_player = None, None
        best_value = -1
        for card_obj, p_index in self.played_cards_log:
            val = get_card_rank(str(card_obj), trump=self.trump_suit)
            if val > best_value:
                best_value = val
                best_card = card_obj
                best_player = p_index
        return best_card, best_player

############################
#         ROUTES           #
############################

@app.route("/", methods=["GET"])
def home():
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
    footer { margin-top: 20px; font-size: 14px; color: #ccc; }
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
    <!-- Player's Hand -->
    <div id="playerHandSection" class="section">
      <h2>Your Hand</h2>
      <div id="playerHand" class="card-row"></div>
    </div>
    <!-- Bidding Section -->
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
    <!-- Trump Selection Section -->
    <div id="trumpSelectionSection" class="section">
      <h2>Select Trump Suit</h2>
      <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <button class="trumpButton" data-suit="Hearts" style="background-color:#e74c3c;">Hearts</button>
        <button class="trumpButton" data-suit="Diamonds" style="background-color:#f1c40f;">Diamonds</button>
        <button class="trumpButton" data-suit="Clubs" style="background-color:#27ae60;">Clubs</button>
        <button class="trumpButton" data-suit="Spades" style="background-color:#2980b9;">Spades</button>
      </div>
    </div>
    <!-- Kitty Section -->
    <div id="kittySection" class="section">
      <h2>Kitty Cards</h2>
      <p>The kitty has been dealt.</p>
      <div id="kittyCards" class="card-row"></div>
      <button id="submitKittyButton">Reveal & Select Kitty Cards</button>
    </div>
    <!-- Discard/Draw Section -->
    <div id="discardSection" class="section">
      <h2>Discard Phase</h2>
      <p id="discardMessage"></p>
      <div id="discardHand" class="card-row"></div>
      <button id="discardButton">Discard Selected Cards</button>
      <button id="skipDiscardButton">Skip Discard</button>
    </div>
    <!-- Trick Phase Section -->
    <div id="trickSection" class="section">
      <h2>Trick Phase</h2>
      <p id="trickResult"></p>
      <div id="currentTrick" class="card-row"></div>
      <p id="playPrompt"></p>
      <button id="playTrickButton">Play Selected Card</button>
    </div>
    <!-- Trick Piles -->
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
      const rank_code = rank === "10" ? "0" : (["J", "Q", "K", "A"].includes(rank) ? rank : rank);
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
              img.classList.toggle("selected-card");
            } else {
              img.classList.toggle("selected-card");
            }
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

    function appendTrickLog(text) {
      const logElem = document.getElementById("trickLog");
      logElem.innerHTML += text + "<br/>";
    }

    function addTrickToPile(trickCards, winner) {
      const pileId = winner === "You" ? "playerTrickPile" : "dealerTrickPile";
      const pile = document.getElementById(pileId);
      trickCards.forEach(card => {
        const img = document.createElement("img");
        // Show the card face in a smaller size:
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

    // 1. Deal Cards
    document.getElementById("dealCardsButton").addEventListener("click", async () => {
      const result = await sendRequest("/deal_cards");
      if (!result) return;
      document.getElementById("dealer").textContent = result.dealer;
      renderHand("playerHand", result.player_hand, true);
      showSection("playerHandSection");
      if (result.dealer === "Player") {
        const compBidResp = await sendRequest("/computer_first_bid");
        if (compBidResp) {
          document.getElementById("computerBid").textContent = `Computer's bid: ${compBidResp.computer_bid}`;
          if (parseInt(compBidResp.computer_bid) === 30) {
            const autoResp = await sendRequest("/submit_bid", { player_bid: 0, computer_bid: 30 });
            if (autoResp) {
              document.getElementById("computerBid").textContent = `Computer's bid: ${autoResp.computer_bid}`;
              hideSection("biddingSection");
              updateTrumpDisplay(autoResp.trump_suit);
              alert(`Computer wins the bid with 30 and selects ${autoResp.trump_suit} as trump.`);
              renderHand("discardHand", [...document.getElementById("playerHand").querySelectorAll("img")].map(img => img.alt), true);
              let excess = document.getElementById("playerHand").querySelectorAll("img").length - 5;
              document.getElementById("discardMessage").textContent = "Please discard exactly " + excess + " card(s).";
              showSection("discardSection");
              return;
            }
          }
        }
      }
      showSection("biddingSection");
    });

    // 2. Bidding with Buttons
    document.querySelectorAll(".bidButton").forEach(btn => {
      btn.addEventListener("click", async () => {
        const bidValue = parseInt(btn.dataset.bid);
        const compBidText = document.getElementById("computerBid").textContent;
        const compBid = compBidText ? parseInt(compBidText.replace("Computer's bid: ", "")) : 0;
        const result = await sendRequest("/submit_bid", { player_bid: bidValue, computer_bid: compBid });
        if (!result) return;
        document.getElementById("computerBid").textContent = `Computer's bid: ${result.computer_bid}`;
        hideSection("biddingSection");
        if (result.bid_winner === "Player") {
          showSection("trumpSelectionSection");
        } else {
          updateTrumpDisplay(result.trump_suit);
          alert(`Computer wins the bid and selects ${result.trump_suit} as trump.`);
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
        alert(`Trump suit set to ${suit}`);
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
      renderHand("discardHand", resp.player_hand, true);
      let excess = resp.player_hand.length - 5;
      document.getElementById("discardMessage").textContent = "Please discard exactly " + excess + " card(s).";
      showSection("discardSection");
    });

    // 4b. Skip Discard
    document.getElementById("skipDiscardButton").addEventListener("click", () => {
      hideSection("discardSection");
      showSection("trickSection");
      if (current_game.leading_player === 1) {
        startTrickIfComputerLeads();
      }
    });

    // 5. Discard & Draw Phase
    document.getElementById("discardButton").addEventListener("click", async () => {
      const selected = [...document.querySelectorAll("#discardHand .selected-card")].map(img => img.alt);
      const playerHandCount = document.getElementById("discardHand").querySelectorAll("img").length;
      const excess = playerHandCount - 5;
      if (selected.length !== excess) {
        alert("Select exactly " + excess + " card(s) to discard.");
        return;
      }
      const resp = await sendRequest("/discard_and_draw", { discarded_cards: selected });
      if (!resp) return;
      renderHand("playerHand", resp.player_hand, true);
      hideSection("discardSection");
      showSection("trickSection");
      if (current_game.leading_player === 1) {
        startTrickIfComputerLeads();
      }
    });

    // 6. Trick Phase – Player plays a card.
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
      updateScoreBoard(resp.player_score, resp.computer_score);
      appendTrickLog(resp.trick_result);
      if (resp.hand_winner) {
        addTrickToPile(resp.current_trick_cards || [], resp.hand_winner);
        alert(`Round over. Winner: ${resp.hand_winner}`);
        // If neither has reached 120, instruct to deal a new hand.
        if (resp.player_score < 120 && resp.computer_score < 120) {
          alert("Click 'Deal Cards' to start a new hand.");
        } else {
          alert(`Game Over! Final Score - You: ${resp.player_score} | Computer: ${resp.computer_score}`);
        }
      }
    });
  </script>
</body>
</html>
    """)

############################
#         SERVER ROUTES     #
############################

@app.route("/attach_kitty", methods=["POST"])
def attach_kitty():
    data = request.json
    keep_cards = data.get("keep_cards", [])
    for card_str in keep_cards:
        for c in current_game.kitty:
            if str(c) == card_str:
                current_game.players[0].hand.append(c)
    current_game.kitty = [c for c in current_game.kitty if str(c) not in keep_cards]
    p_hand = [str(c) for c in current_game.players[0].hand]
    return jsonify({"player_hand": p_hand})

@app.route("/deal_cards", methods=["POST"])
def deal_cards():
    global current_game, current_dealer
    current_game = Game()
    current_game.deal_hands()
    old_dealer = current_dealer
    current_dealer = "Computer" if current_dealer == "Player" else "Player"
    p_hand = [str(c) for c in current_game.players[0].hand]
    return jsonify({"player_hand": p_hand, "dealer": old_dealer})

@app.route("/computer_first_bid", methods=["POST"])
def computer_first_bid():
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def submit_bid():
    try:
        if current_game is None:
            return jsonify({"error": "No game in progress. Please deal cards first."}), 400
        data = request.json
        player_bid = data.get("player_bid", 0)
        comp_bid = data.get("computer_bid", 0)
        if player_bid == 0:
            comp_bid = random.choice([15, 20, 25, 30])
        if comp_bid > player_bid:
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            current_game.bid_winner = 1
            current_game.leading_player = 1
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer", "trump_suit": trump_suit, "kitty_cards": kitty})
        else:
            current_game.bid_winner = 0
            current_game.leading_player = 0
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})
    except Exception as e:
        print("Error in /submit_bid:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/select_trump", methods=["POST"])
def select_trump():
    data = request.json
    suit = data.get("trump_suit", "Hearts")
    kitty = current_game.confirm_trump(suit)
    return jsonify({"kitty_cards": kitty, "trump_suit": suit})

@app.route("/discard_and_draw", methods=["POST"])
def discard_and_draw():
    data = request.json
    discards = data.get("discarded_cards", [])
    result = current_game.discard_and_draw(0, discards)
    if "error" in result:
        return jsonify(result), 400
    p_hand = [str(c) for c in current_game.players[0].hand]
    return jsonify({"player_hand": p_hand})

@app.route("/play_trick", methods=["POST"])
def play_trick():
    data = request.json
    played_card = data.get("played_card")
    result_obj, hand_winner = current_game.play_trick(played_card)
    p_hand = [str(c) for c in current_game.players[0].hand]
    resp = {
        "trick_result": result_obj.get("trick_result", ""),
        "player_hand": p_hand,
        "hand_winner": hand_winner,
        "player_score": current_game.players[0].score,
        "computer_score": current_game.players[1].score
    }
    if "computer_card" in result_obj:
        resp["computer_card"] = result_obj["computer_card"]
    if "current_trick_cards" in result_obj:
        resp["current_trick_cards"] = result_obj["current_trick_cards"]
    return jsonify(resp)

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
