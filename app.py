from flask import Flask, request, jsonify, render_template_string, send_from_directory
import random, os

app = Flask(__name__)

############################
#        GAME LOGIC        #
############################

# Global game state and dealer toggling.
current_game = None
current_dealer = "Player"  # toggles each round

# Basic ranking table for non-trump (and for trump Hearts)
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
    If trump is Diamonds, Clubs, or Spades then a trump ranking dictionary is used:
      - For example, if trump is Diamonds:
            "5 of Diamonds": 200,
            "J of Diamonds": 199,
            "A of Hearts": 198 (the Ace of Hearts is treated as trump, third highest),
            then the remaining Diamond cards follow.
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

# --- Using Deck of Cards API for images ---
def getCardImageUrl(card):
    """
    Converts a card string (e.g., "J of Hearts") to the Deck of Cards API URL.
    For example, "J of Hearts" becomes "https://deckofcardsapi.com/static/img/JH.png".
    Note: For "10", use "0" (Deck of Cards API uses "0" for 10).
    """
    parts = card.split(" of ")
    if len(parts) != 2:
        return ""
    rank, suit = parts
    rank_code = "0" if rank == "10" else (rank if rank in ["J", "Q", "K", "A"] else rank)
    suit_code = suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

def getCardBackUrl():
    """Returns the URL for the back of a playing card from the Deck of Cards API."""
    return "https://deckofcardsapi.com/static/img/back.png"

# --- End of image functions ---

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
        self.leading_player = None  # set to bid winner initially
        self.trick_count = 0
        self.played_cards_log = []  # list of tuples (card, player_index)
        self.trick_log_text = ""
        self.current_lead_suit = None
    def deal_hands(self):
        self.kitty = self.deck.deal(3)
        for p in self.players:
            p.hand = []
            p.tricks_won = 0
        self.players[0].add_to_hand(self.deck.deal(5))
        self.players[1].add_to_hand(self.deck.deal(5))
    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]
    def discard_and_draw(self, player_index, discards):
        p = self.players[player_index]
        p.discard_cards(discards)
        needed = 5 - len(p.hand)
        if needed > 0:
            p.add_to_hand(self.deck.deal(needed))
    def attach_kitty(self, player_index, keep_list):
        p = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    p.hand.append(c)
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        return [str(c) for c in p.hand]
    def play_trick(self, played_card=None):
        """
        Trick Phase with Follow Suit & Reneging:
         - When the computer leads (bid winner is Computer), if no played_card is provided,
           it automatically plays its lead card and returns it (so the client can display its image).
         - Then the player selects a card from their hand. If the player has any card in the lead suit,
           they must follow suit unless they play a renegable trump.
         - (Renegable trump cards: the 5 or Jack of trump can be played at any time; if trump is Hearts,
           the Ace of Hearts is renegable only if the opponent is not playing the 5 or Jack.)
         - If the player leads, the computer attempts to follow suit.
         - The played card is removed from the player's hand.
         - Each trick win gives 5 points; after 5 tricks (or if the hand is empty), a bonus 10 points is awarded
           for the highest-ranking card.
         - A cumulative trick log is maintained.
        """
        def is_renegable(card_str, trump):
            if card_str == f"5 of {trump}" or card_str == f"J of {trump}":
                return True
            if trump == "Hearts" and card_str == "A of Hearts":
                return True
            return False

        # --- Computer leads ---
        if self.leading_player == 1:
            if played_card is None:
                if len(self.players[1].hand) == 0:
                    return {"trick_result": "Computer has no card to lead.", "computer_card": None}, None
                comp_card = self.players[1].hand.pop(0)
                self.current_lead_suit = comp_card.suit
                self.played_cards_log.append((comp_card, 1))
                self.trick_log_text += f"Computer leads with {comp_card}. "
                # Return computer's card for image display.
                return {"trick_result": "", "computer_card": str(comp_card)}, None
            else:
                if played_card not in [str(c) for c in self.players[0].hand]:
                    return {"trick_result": "Invalid card."}, None
                player_card = next(c for c in self.players[0].hand if str(c) == played_card)
                if any(c.suit == self.current_lead_suit for c in self.players[0].hand):
                    if player_card.suit != self.current_lead_suit:
                        if not (player_card.suit == self.trump_suit and is_renegable(str(player_card), self.trump_suit)):
                            return {"trick_result": f"You must follow suit ({self.current_lead_suit})."}, None
                self.players[0].hand.remove(player_card)
                self.played_cards_log.append((player_card, 0))
                self.trick_log_text += f"You played {player_card}. "
                comp_card, _ = self.played_cards_log[0]
                rank_player = get_card_rank(str(player_card), trump=self.trump_suit)
                rank_comp = get_card_rank(str(comp_card), trump=self.trump_suit)
                winner = 0 if rank_player > rank_comp else 1
                if winner == 0:
                    self.trick_log_text += "You win the trick! "
                else:
                    self.trick_log_text += "Computer wins the trick! "
                self.players[winner].score += 5
                self.players[winner].tricks_won += 1
                self.leading_player = winner
                self.trick_count += 1
                self.played_cards_log = []
                self.current_lead_suit = None
                if self.trick_count >= 5 or len(self.players[0].hand) == 0:
                    best_card, best_player = self.get_highest_card()
                    self.players[best_player].score += 10
                    self.trick_log_text += f"Round over! Highest card was {best_card}. Scores: You {self.players[0].score} | Computer {self.players[1].score}."
                    round_winner = "You" if self.players[0].score > self.players[1].score else "Computer"
                    return {"trick_result": self.trick_log_text}, round_winner
                return {"trick_result": self.trick_log_text}, None

        # --- Player leads ---
        else:
            if played_card is None:
                return {"trick_result": "Your turn to lead. Please select a card."}, None
            if played_card not in [str(c) for c in self.players[0].hand]:
                return {"trick_result": "Invalid card."}, None
            player_card = next(c for c in self.players[0].hand if str(c) == played_card)
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
            else:
                self.trick_log_text += "Computer wins the trick! "
            self.played_cards_log = []
            self.current_lead_suit = None
            if self.trick_count >= 5 or len(self.players[0].hand) == 0:
                best_card, best_player = self.get_highest_card()
                self.players[best_player].score += 10
                self.trick_log_text += f"Round over! Highest card was {best_card}. Scores: You {self.players[0].score} | Computer {self.players[1].score}."
                round_winner = "You" if self.players[0].score > self.players[1].score else "Computer"
                return {"trick_result": self.trick_log_text}, round_winner
            return {"trick_result": self.trick_log_text}, None

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
    body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; margin: 0; padding: 0; }
    #gameContainer { max-width: 800px; margin: 50px auto; padding: 20px; background-color: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    .card-row { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
    .card-image { width: 60px; height: auto; cursor: pointer; border: 2px solid transparent; border-radius: 8px; }
    .selected-card { border-color: #007bff; }
    button { margin: 10px; padding: 10px 20px; font-size: 16px; cursor: pointer; }
    .section { margin: 20px 0; display: none; }
    #scoreBoard { font-weight: bold; margin-bottom: 10px; }
    #trumpDisplay { margin-bottom: 10px; }
    #trumpDisplay img { width: 40px; height: auto; vertical-align: middle; }
    #computerCardSection { margin: 10px 0; }
    footer { margin-top: 20px; font-size: 14px; color: #666; }
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
    <!-- Unified Hand Display -->
    <div id="playerHandSection" class="section">
      <h2>Your Hand</h2>
      <div id="playerHand" class="card-row"></div>
    </div>
    <!-- Bidding Section with Bid Buttons -->
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
        <button class="trumpButton" data-suit="Hearts" style="padding:10px 20px;">Hearts</button>
        <button class="trumpButton" data-suit="Diamonds" style="padding:10px 20px;">Diamonds</button>
        <button class="trumpButton" data-suit="Clubs" style="padding:10px 20px;">Clubs</button>
        <button class="trumpButton" data-suit="Spades" style="padding:10px 20px;">Spades</button>
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
      <h2>Select 1-4 Cards to Discard (to finalize your 5-card hand)</h2>
      <div id="discardHand" class="card-row"></div>
      <button id="discardButton">Discard & Draw</button>
      <button id="skipDiscardButton">Skip Discard</button>
    </div>
    <!-- Trick Phase Section -->
    <div id="trickSection" class="section">
      <h2>Trick Phase</h2>
      <p id="trickResult"></p>
      <div id="computerCardSection" class="card-row"></div>
      <p id="playPrompt"></p>
      <button id="playTrickButton">Play Selected Card</button>
      <h3>Trick Log</h3>
      <p id="trickLog"></p>
    </div>
    <footer>&copy; O'Donohue Software</footer>
  </div>

  <script>
    // Global variable for current scores.
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
      // Convert a card string like "J of Hearts" to a Deck of Cards API URL.
      const parts = card.split(" of ");
      if (parts.length !== 2) return "";
      let [rank, suit] = parts;
      const rank_code = rank === "10" ? "0" : (rank in {"J":1, "Q":1, "K":1, "A":1} ? rank : rank);
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
                if (i !== img) i.classList.remove("selected-card");
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
            if (i !== img) i.classList.remove("selected-card");
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
      const trumpDiv = document.getElementById("trumpDisplay");
      trumpDiv.innerHTML = `<span>Trump: </span><img src="${getCardImageUrl('5 of ' + suit)}" alt="5 of ${suit}" />`;
    }

    function appendTrickLog(text) {
      const logElem = document.getElementById("trickLog");
      logElem.innerHTML += text + "<br/>";
    }

    // When computer leads, fetch and display its lead card.
    async function startTrickIfComputerLeads() {
      const leadResp = await sendRequest("/play_trick", { played_card: null });
      if (leadResp) {
        if (leadResp.computer_card) {
          renderHand("computerCardSection", [leadResp.computer_card], false);
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
      // If player is the dealer, computer bids first.
      if (result.dealer === "Player") {
        const compBidResp = await sendRequest("/computer_first_bid");
        if (compBidResp) {
          document.getElementById("computerBid").textContent = `Computer's bid: ${compBidResp.computer_bid}`;
          // If computer's bid is 30, auto-submit (player does not bid)
          if (parseInt(compBidResp.computer_bid) === 30) {
            // Auto-submit with player bid = 0 (pass)
            const autoResp = await sendRequest("/submit_bid", { player_bid: 0, computer_bid: 30 });
            if (autoResp) {
              document.getElementById("computerBid").textContent = `Computer's bid: ${autoResp.computer_bid}`;
              hideSection("biddingSection");
              updateTrumpDisplay(autoResp.trump_suit);
              alert(`Computer wins the bid with 30 and selects ${autoResp.trump_suit} as trump.`);
              renderHand("discardHand", [...document.getElementById("playerHand").querySelectorAll("img")].map(img => img.alt), true);
              showSection("discardSection");
              return;
            }
          }
        }
      }
      showSection("biddingSection");
    });

    // 2. Bidding: Use clickable bid buttons.
    document.querySelectorAll(".bidButton").forEach(btn => {
      btn.addEventListener("click", async () => {
        const bidValue = parseInt(btn.dataset.bid);
        // Get the computer's bid from the displayed text
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
          showSection("discardSection");
        }
      });
    });

    // 3. Trump Selection (improved UI)
    document.querySelectorAll(".trumpButton").forEach(btn => {
      btn.addEventListener("click", async () => {
        const suit = btn.dataset.suit;
        const resp = await sendRequest("/select_trump", { trump_suit: suit });
        if (!resp) return;
        updateTrumpDisplay(suit);
        alert(`Trump suit set to ${suit}`);
        hideSection("trumpSelectionSection");
        // Show kitty cards as card backs.
        renderKittyCards("kittyCards", resp.kitty_cards);
        showSection("kittySection");
      });
    });

    // 4. Submit Kitty Selection – reveal kitty cards and merge into hand.
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
      // Force a discard/draw phase even if hand is 5 cards.
      renderHand("discardHand", resp.player_hand, true);
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
      if (selected.length < 1 || selected.length > 4) {
        alert("Select between 1 and 4 cards to discard.");
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

    // 6. Trick Phase – player plays a card.
    document.getElementById("playTrickButton").addEventListener("click", async () => {
      const selected = document.querySelector("#playerHand .selected-card");
      let cardStr = selected ? selected.alt : null;
      const resp = await sendRequest("/play_trick", { played_card: cardStr });
      if (!resp) return;
      document.getElementById("trickResult").textContent = resp.trick_result;
      renderHand("playerHand", resp.player_hand, true);
      updateScoreBoard(resp.player_score, resp.computer_score);
      appendTrickLog(resp.trick_result);
      if (resp.hand_winner) {
        alert(`Round over. Winner: ${resp.hand_winner}`);
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
    current_game.discard_and_draw(0, discards)
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
    return jsonify(resp)

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
