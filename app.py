import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                      1) CARD RANK LOOKUPS (Forty-Fives)                     #
###############################################################################

TRUMP_DIAMONDS = {
    "5 of Diamonds": 200, "J of Diamonds": 199, "A of Hearts": 198, "A of Diamonds": 197,
    "K of Diamonds": 196, "Q of Diamonds": 195, "10 of Diamonds": 194, "9 of Diamonds": 193,
    "8 of Diamonds": 192, "7 of Diamonds": 191, "6 of Diamonds": 190,
    "4 of Diamonds": 189, "3 of Diamonds": 188, "2 of Diamonds": 187
}
TRUMP_HEARTS = {
    "5 of Hearts": 200, "J of Hearts": 199, "A of Hearts": 198,
    "K of Hearts": 196, "Q of Hearts": 195, "10 of Hearts": 194, "9 of Hearts": 193,
    "8 of Hearts": 192, "7 of Hearts": 191, "6 of Hearts": 190,
    "4 of Hearts": 189, "3 of Hearts": 188, "2 of Hearts": 187
}
TRUMP_CLUBS = {
    "5 of Clubs": 200, "J of Clubs": 199, "A of Hearts": 198, "A of Clubs": 197,
    "K of Clubs": 196, "Q of Clubs": 195,
    "2 of Clubs": 194, "3 of Clubs": 193, "4 of Clubs": 192,
    "6 of Clubs": 191, "7 of Clubs": 190, "8 of Clubs": 189,
    "9 of Clubs": 188, "10 of Clubs": 187
}
TRUMP_SPADES = {
    "5 of Spades": 200, "J of Spades": 199, "A of Hearts": 198, "A of Spades": 197,
    "K of Spades": 196, "Q of Spades": 195,
    "2 of Spades": 194, "3 of Spades": 193, "4 of Spades": 192,
    "6 of Spades": 191, "7 of Spades": 190, "8 of Spades": 189,
    "9 of Spades": 188, "10 of Spades": 187
}
OFFSUIT_DIAMONDS = {
    "K of Diamonds": 200, "Q of Diamonds": 199, "J of Diamonds": 198, "10 of Diamonds": 197,
    "9 of Diamonds": 196, "8 of Diamonds": 195, "7 of Diamonds": 194, "6 of Diamonds": 193,
    "5 of Diamonds": 192, "4 of Diamonds": 191, "3 of Diamonds": 190, "2 of Diamonds": 189,
    "A of Diamonds": 188
}
OFFSUIT_HEARTS = {
    "K of Hearts": 200, "Q of Hearts": 199, "J of Hearts": 198, "10 of Hearts": 197,
    "9 of Hearts": 196, "8 of Hearts": 195, "7 of Hearts": 194, "6 of Hearts": 193,
    "5 of Hearts": 192, "4 of Hearts": 191, "3 of Hearts": 190, "2 of Hearts": 189
}
OFFSUIT_CLUBS = {
    "K of Clubs": 200, "Q of Clubs": 199, "J of Clubs": 198, "A of Clubs": 197,
    "2 of Clubs": 196, "3 of Clubs": 195, "4 of Clubs": 194, "5 of Clubs": 193,
    "6 of Clubs": 192, "7 of Clubs": 191, "8 of Clubs": 190, "9 of Clubs": 189,
    "10 of Clubs": 188
}
OFFSUIT_SPADES = {
    "K of Spades": 200, "Q of Spades": 199, "J of Spades": 198, "A of Spades": 197,
    "2 of Spades": 196, "3 of Spades": 195, "4 of Spades": 194, "5 of Spades": 193,
    "6 of Spades": 192, "7 of Spades": 191, "8 of Spades": 190, "9 of Spades": 189,
    "10 of Spades": 188
}

def get_card_rank(card_str: str, trump_suit: str) -> int:
    if trump_suit == "Diamonds":
        if card_str in TRUMP_DIAMONDS:
            return TRUMP_DIAMONDS[card_str]
        else:
            if card_str.endswith("Hearts"):
                return OFFSUIT_HEARTS.get(card_str, 0)
            elif card_str.endswith("Clubs"):
                return OFFSUIT_CLUBS.get(card_str, 0)
            elif card_str.endswith("Spades"):
                return OFFSUIT_SPADES.get(card_str, 0)
            else:
                return 0
    elif trump_suit == "Hearts":
        if card_str in TRUMP_HEARTS:
            return TRUMP_HEARTS[card_str]
        else:
            if card_str.endswith("Diamonds"):
                return OFFSUIT_DIAMONDS.get(card_str, 0)
            elif card_str.endswith("Clubs"):
                return OFFSUIT_CLUBS.get(card_str, 0)
            elif card_str.endswith("Spades"):
                return OFFSUIT_SPADES.get(card_str, 0)
            else:
                return 0
    elif trump_suit == "Clubs":
        if card_str in TRUMP_CLUBS:
            return TRUMP_CLUBS[card_str]
        else:
            if card_str.endswith("Diamonds"):
                return OFFSUIT_DIAMONDS.get(card_str, 0)
            elif card_str.endswith("Hearts"):
                return OFFSUIT_HEARTS.get(card_str, 0)
            elif card_str.endswith("Spades"):
                return OFFSUIT_SPADES.get(card_str, 0)
            else:
                return 0
    elif trump_suit == "Spades":
        if card_str in TRUMP_SPADES:
            return TRUMP_SPADES[card_str]
        else:
            if card_str.endswith("Diamonds"):
                return OFFSUIT_DIAMONDS.get(card_str, 0)
            elif card_str.endswith("Hearts"):
                return OFFSUIT_HEARTS.get(card_str, 0)
            elif card_str.endswith("Clubs"):
                return OFFSUIT_CLUBS.get(card_str, 0)
            else:
                return 0
    return 0

###############################################################################
#                     2) CARD IMAGE HELPERS (deckofcardsapi)                  #
###############################################################################

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    """Convert '10 of Hearts' -> 'https://deckofcardsapi.com/static/img/0H.png', etc."""
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return card_back_url()
    rank, suit = parts
    suit_letter = suit[0].upper()
    if rank == "10":
        rank_code = "0"
    else:
        rank_code = rank.upper()[:1]  # e.g. 'A', 'K', 'Q', 'J', '2', '3'...
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_letter}.png"

###############################################################################
#                    3) CLASSES: Card, Deck, Player, Game                     #
###############################################################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(s, r) for s in suits for r in ranks]
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
        self.hand = []
        self.score = 0
        self.tricks_won = 0

    def add_to_hand(self, cards):
        self.hand.extend(cards)

class Game:
    def __init__(self):
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card_played = None
        self.highest_card_owner = None

        # For UI: track last trick played
        self.last_played_cards = []  # e.g. [("You", "K of Hearts"), ("Computer", "7 of Hearts")]
        self.kitty_revealed = False  # True if user won bid & is selecting kitty

    def reset_round_state(self):
        self.deck = Deck()
        self.kitty.clear()
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card_played = None
        self.highest_card_owner = None
        self.last_played_cards = []
        self.kitty_revealed = False
        for p in self.players:
            p.hand.clear()
            p.tricks_won = 0

    def deal_hands(self, dealer_index=1):
        self.deck.shuffle()
        for p in self.players:
            p.hand.clear()
        self.kitty.clear()
        # 3 each, then kitty(3), then 2 each
        eldest = 0 if dealer_index == 1 else 1
        self.players[eldest].add_to_hand(self.deck.deal(3))
        self.players[dealer_index].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[eldest].add_to_hand(self.deck.deal(2))
        self.players[dealer_index].add_to_hand(self.deck.deal(2))

    def perform_bidding(self, dealer_index=1, player_bid=0):
        comp_bid = random.choice([0, 15, 20, 25, 30])
        eldest = 0 if dealer_index == 1 else 1
        if eldest == 0:
            p0_bid = player_bid
            p1_bid = comp_bid
        else:
            p0_bid = comp_bid
            p1_bid = player_bid
        if p0_bid == 0 and p1_bid == 0:
            if dealer_index == 1:
                p1_bid = 15
            else:
                p0_bid = 15
        if p0_bid > p1_bid:
            self.bid_winner = 0
            self.bid = p0_bid
        else:
            self.bid_winner = 1
            self.bid = p1_bid

    def set_trump_suit(self, suit):
        self.trump_suit = suit

    def reveal_kitty_for_user_selection(self):
        """
        Called if user is the bidder & we want to show the kitty face-up so user can pick which cards to keep.
        Just flip a flag for the UI. The actual "attaching" (keeping cards, discarding extras) will happen
        once the user finalizes selections.
        """
        self.kitty_revealed = True

    def finalize_kitty_selection(self, keep_kitty_cards, discard_from_hand):
        """
        Called by the user after they've selected which kitty cards to keep
        and which existing hand cards to discard.
        We remove 'discard_from_hand' from the player's hand, add 'keep_kitty_cards' from the kitty,
        then discard the rest of the kitty.
        """
        bidder = self.players[self.bid_winner]
        # remove the discarded hand cards from bidder's hand
        new_hand = []
        for c in bidder.hand:
            if str(c) not in discard_from_hand:
                new_hand.append(c)
        bidder.hand = new_hand

        # from the kitty, add the ones we want to keep
        kitty_to_keep = []
        kitty_to_discard = []
        for c in self.kitty:
            if str(c) in keep_kitty_cards:
                kitty_to_keep.append(c)
            else:
                kitty_to_discard.append(c)

        bidder.hand.extend(kitty_to_keep)
        self.kitty = kitty_to_discard  # leftover in kitty => effectively "discarded"

        # For safety, if bidder's hand > 5, still discard down
        while len(bidder.hand) > 5:
            bidder.hand.pop()

        # Mark kitty as not revealed
        self.kitty_revealed = False

    def computer_attach_kitty(self):
        """
        If the computer is bidder, it just does a naive approach: keep all trump.
        """
        bidder = self.players[self.bid_winner]
        bidder.hand.extend(self.kitty)
        self.kitty.clear()
        # discard non-trump
        def is_trump_or_ace_hearts(c):
            if c.suit == self.trump_suit:
                return True
            if c.suit == "Hearts" and c.rank == "A":
                return True
            return False
        bidder.hand.sort(
            key=lambda card: (is_trump_or_ace_hearts(card), get_card_rank(str(card), self.trump_suit)),
            reverse=True
        )
        while len(bidder.hand) > 5:
            bidder.hand.pop()

    def allow_other_player_discard(self):
        """
        The non-bidder can also discard. We'll do a naive approach.
        """
        for i, p in enumerate(self.players):
            if i == self.bid_winner:
                continue
            p.hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
            while len(p.hand) > 5:
                p.hand.pop()

    def play_card_user(self, card_str):
        """
        The user clicked a card to lead or follow. If it's user's turn, remove that card from the user hand.
        Then the computer responds, we figure out winner.
        """
        user = self.players[0]
        if card_str not in [str(c) for c in user.hand]:
            return f"Error: {card_str} not in your hand"

        # user leads or follows
        user_card = next(c for c in user.hand if str(c) == card_str)
        user.hand.remove(user_card)

        # Build "last_played_cards" for UI
        self.last_played_cards = [(user.name, str(user_card))]

        # If user is leading
        if self.leading_player == 0:
            # Computer responds
            comp_respond_str = self.computer_follow_card(self.players[1], user_card.suit)
            comp_card_obj = next(c for c in self.players[1].hand if str(c) == comp_respond_str)
            self.players[1].hand.remove(comp_card_obj)

            self.last_played_cards.append((self.players[1].name, comp_respond_str))

            winner_index = self.evaluate_trick_winner([
                (0, user_card),
                (1, comp_card_obj)
            ])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            self.leading_player = winner_index
            return f"You led {card_str}, Computer played {comp_respond_str} -> Winner: {self.players[winner_index].name}"
        else:
            # That means the computer is leading
            lead_card_str = self.computer_select_lead_card(self.players[1].hand)
            lead_card_obj = next(c for c in self.players[1].hand if str(c) == lead_card_str)
            self.players[1].hand.remove(lead_card_obj)
            self.last_played_cards = [(self.players[1].name, lead_card_str), (user.name, card_str)]

            winner_index = self.evaluate_trick_winner([
                (1, lead_card_obj),
                (0, user_card)
            ])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            self.leading_player = winner_index
            return f"Computer led {lead_card_str}, You played {card_str} -> Winner: {self.players[winner_index].name}"

    def computer_select_lead_card(self, comp_hand):
        if not comp_hand:
            return None
        comp_hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
        return str(comp_hand[0])

    def computer_follow_card(self, player_obj, lead_suit):
        # naive follow suit if possible
        valid_cards = [c for c in player_obj.hand if c.suit == lead_suit]
        if valid_cards:
            valid_cards.sort(key=lambda x: get_card_rank(str(x), self.trump_suit), reverse=True)
            return str(valid_cards[0])
        else:
            player_obj.hand.sort(key=lambda x: get_card_rank(str(x), self.trump_suit))
            return str(player_obj.hand[-1])

    def evaluate_trick_winner(self, played_cards):
        if not played_cards:
            return 0
        lead_suit = played_cards[0][1].suit
        trump_cards = []
        for pid, card_obj in played_cards:
            rank_val = get_card_rank(str(card_obj), self.trump_suit)
            if rank_val >= 100:
                trump_cards.append((pid, card_obj))
        if trump_cards:
            winner_pid, winner_card = max(trump_cards, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
        else:
            same_suit_cards = [(pid, c) for (pid, c) in played_cards if c.suit == lead_suit]
            winner_pid, winner_card = max(same_suit_cards, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))

        # track highest card for bonus
        val_winner = get_card_rank(str(winner_card), self.trump_suit)
        if self.highest_card_played is None or val_winner > get_card_rank(self.highest_card_played, self.trump_suit):
            self.highest_card_played = str(winner_card)
            self.highest_card_owner = winner_pid

        return winner_pid

    def finalize_hand(self):
        # Bonus
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5

        bidder = self.players[self.bid_winner]
        bidder_points_this_round = bidder.tricks_won * 5
        if self.highest_card_owner == self.bid_winner:
            bidder_points_this_round += 5
        if bidder_points_this_round < self.bid:
            bidder.score -= self.bid

        result = {"game_over": False, "winner": None}
        s0 = self.players[0].score
        s1 = self.players[1].score
        if s0 >= 120 and s1 >= 120:
            result["game_over"] = True
            result["winner"] = self.players[self.bid_winner].name
        elif s0 >= 120:
            result["game_over"] = True
            result["winner"] = self.players[0].name
        elif s1 >= 120:
            result["game_over"] = True
            result["winner"] = self.players[1].name
        return result

###############################################################################
#                 4) FLASK GLOBALS & ROUTES: "Card Table" UI                  #
###############################################################################

current_game = None
dealer_index = 1  # We'll fix the dealer as "Computer" for demonstration
round_trick_count = 0

@app.route("/", methods=["GET"])
def index():
    """
    A simple HTML/JS UI that mimics sitting around a card table:
     - Table background
     - Your hand at bottom, face-up
     - Computer's hand at top, face-down
     - Kitty area on one side
     - Middle area shows last played cards
     - When user wins bid, they see kitty face-up and can select which cards to keep, which to discard
    """
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Forty-Fives - "Around the Table" UI</title>
    <style>
      body {
        margin: 0; padding: 0;
        background-color: green; /* table color */
        font-family: sans-serif;
      }
      #app {
        display: flex; flex-direction: column;
        height: 100vh;
        color: white;
      }
      #topRow, #bottomRow {
        flex: 0 0 auto; /* fixed height segments */
        text-align: center;
        padding: 10px;
      }
      #tableArea {
        flex: 1 1 auto; display: flex; flex-direction: row;
        justify-content: space-around;
        align-items: center;
        position: relative;
      }
      #computerArea {
        position: absolute; top: 20px; width: 100%; text-align: center;
      }
      .cardRow {
        display: inline-flex;
      }
      .cardImg {
        width: 75px; margin: 3px; border-radius: 5px; cursor: pointer;
      }
      #kittyArea {
        position: absolute; left: 20px; text-align: center;
        top: 50%; transform: translateY(-50%);
      }
      #centerPlay {
        text-align: center;
      }
      #playerArea {
        position: absolute; bottom: 20px; width: 100%; text-align: center;
      }
      .logBox {
        background: rgba(0,0,0,0.4);
        padding: 8px; margin: 8px;
        max-height: 150px; overflow-y: auto;
      }
      #scoreBox {
        margin: 10px auto; width: 80%; text-align: center;
      }
      .selectedCard {
        outline: 3px solid yellow;
      }
      .hidden {
        display: none;
      }
      button {
        margin: 5px; padding: 5px 10px; border: none; border-radius: 4px;
        background: #555; color: #fff; cursor: pointer;
      }
      button:hover {
        background: #666;
      }
    </style>
</head>
<body>
<div id="app">
  <div id="topRow">
    <button onclick="newRound()">New Round</button>
    <button onclick="showState()">Refresh State</button>
    <button onclick="finalizeRound()">Finalize Round</button>
    <button onclick="toggleLog()">Toggle Log</button>
    <br>
    <label>Bid: </label>
    <select id="bidSelect">
      <option value="0">Pass</option>
      <option value="15">15</option>
      <option value="20">20</option>
      <option value="25">25</option>
      <option value="30">30</option>
    </select>
    <button onclick="submitBid()">Submit Bid</button>

    <label>Trump: </label>
    <select id="trumpSelect">
      <option>Hearts</option>
      <option>Diamonds</option>
      <option>Clubs</option>
      <option>Spades</option>
    </select>
    <button onclick="selectTrump()">Set Trump</button>
  </div>

  <div id="tableArea">
    <div id="computerArea">
      <div>Computer's Hand</div>
      <div id="computerHand" class="cardRow"></div>
    </div>

    <div id="kittyArea">
      <div>Kitty</div>
      <div id="kittyCards" class="cardRow"></div>
      <button id="confirmKittyBtn" class="hidden" onclick="confirmKittyDiscard()">Confirm Kitty & Discards</button>
    </div>

    <div id="centerPlay">
      <div id="playedCards" class="cardRow"></div>
      <div class="logBox" id="trickLog"></div>
      <div id="scoreBox"></div>
    </div>
  </div>

  <div id="playerArea">
    <div>Your Hand</div>
    <div id="playerHand" class="cardRow"></div>
    <div class="logBox hidden" id="log"></div>
  </div>
</div>

<script>
let selectedCards = [];  // for kitty selection or discarding
let kittyCards = [];     // store kitty card objects from server
let yourCards = [];      // store your card objects
let computerCardCount = 0;
let lastPlayed = [];     // store last trick from server

// toggles for kitty selection
let kittyRevealed = false;
let isBidWinner = false;
let kittyAttached = false;

// toggles for user leading or not
// We'll let the user click on a card to play it if it's user leading.
let userLeading = false;

let showLogPanel = false;

function toggleLog() {
  showLogPanel = !showLogPanel;
  document.getElementById('log').classList.toggle('hidden', !showLogPanel);
}

function log(msg) {
  let logDiv = document.getElementById('log');
  logDiv.textContent += msg + "\\n";
  logDiv.scrollTop = logDiv.scrollHeight;
}

function newRound() {
  fetch('/new_round', {method:'POST'})
    .then(r=>r.json())
    .then(data=>{
      log("New Round: " + JSON.stringify(data));
      showState();
    });
}

function submitBid() {
  let val = parseInt(document.getElementById('bidSelect').value);
  fetch('/bid', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({player_bid: val})
  })
  .then(r=>r.json())
  .then(data=>{
    log("Bid result: " + JSON.stringify(data));
    showState();
  });
}

function selectTrump() {
  let suit = document.getElementById('trumpSelect').value;
  fetch('/select_trump', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ suit })
  })
  .then(r=>r.json())
  .then(data=>{
    log("Trump: " + JSON.stringify(data));
    showState();
  });
}

function showState() {
  fetch('/show_state')
    .then(r=>r.json())
    .then(data=>{
      if(data.error) {
        log("Error: " + data.error);
        return;
      }
      // update global
      yourCards = data.your_cards;
      computerCardCount = data.computer_count;
      kittyCards = data.kitty;
      kittyRevealed = data.kitty_revealed;
      isBidWinner = data.is_bid_winner;
      userLeading = data.user_leading;
      kittyAttached = data.kitty_attached;

      // display
      displayPlayerHand();
      displayComputerHand();
      displayKitty();
      displayScores(data);
      displayPlayedCards(data.last_played_cards, data.trick_message);

      // If user is the bidder and kitty is revealed => show "Confirm" button
      let confirmBtn = document.getElementById('confirmKittyBtn');
      confirmBtn.classList.toggle('hidden', !(isBidWinner && kittyRevealed));
    });
}

function displayPlayerHand() {
  let handDiv = document.getElementById('playerHand');
  handDiv.innerHTML = "";
  yourCards.forEach(cardObj => {
    let img = document.createElement('img');
    img.src = cardObj.img;
    img.className = "cardImg";
    img.setAttribute('data-card', cardObj.name);
    // If user can discard or click to play:
    if(kittyRevealed || userLeading) {
      img.onclick = () => handleCardClick(cardObj.name);
      // highlight if selected
      if(selectedCards.includes(cardObj.name)) {
        img.classList.add('selectedCard');
      }
    }
    handDiv.appendChild(img);
  });
}

function displayComputerHand() {
  let compDiv = document.getElementById('computerHand');
  compDiv.innerHTML = "";
  for(let i=0; i<computerCardCount; i++){
    let img = document.createElement('img');
    img.src = dataBackUrl();
    img.className = "cardImg";
    compDiv.appendChild(img);
  }
}

function displayKitty() {
  let kittyDiv = document.getElementById('kittyCards');
  kittyDiv.innerHTML = "";
  // if kitty is revealed, show them face-up
  if(kittyRevealed) {
    kittyCards.forEach(cardObj => {
      let img = document.createElement('img');
      img.src = cardObj.img;
      img.className = "cardImg";
      img.setAttribute('data-card', cardObj.name);
      img.onclick = () => handleKittyCardClick(cardObj.name);
      if(selectedCards.includes(cardObj.name)) {
        img.classList.add('selectedCard');
      }
      kittyDiv.appendChild(img);
    });
  } else {
    // face-down
    kittyCards.forEach(_ => {
      let img = document.createElement('img');
      img.src = dataBackUrl();
      img.className = "cardImg";
      kittyDiv.appendChild(img);
    });
  }
}

function displayScores(info) {
  let scoreBox = document.getElementById('scoreBox');
  scoreBox.innerHTML = `You: ${info.your_score} | Computer: ${info.computer_score} <br>
    Bid Winner: ${info.bid_winner} (bid=${info.bid_amount}), Trump: ${info.trump_suit || '(none)'} <br>
    Tricks Played: ${info.tricks_played}`;
}

function displayPlayedCards(playedList, msg) {
  let centerDiv = document.getElementById('playedCards');
  centerDiv.innerHTML = "";
  if(playedList && playedList.length>0) {
    playedList.forEach(pl => {
      // pl => [playerName, cardName, cardImg]
      let img = document.createElement('img');
      img.src = pl[2];
      img.className = "cardImg";
      centerDiv.appendChild(img);
    });
  }
  document.getElementById('trickLog').textContent = msg || "";
}

// Handle user clicking card in their hand
function handleCardClick(cardName) {
  if(kittyRevealed) {
    // user is discarding or picking kitty -> toggle selection
    if(selectedCards.includes(cardName)) {
      selectedCards = selectedCards.filter(c => c !== cardName);
    } else {
      selectedCards.push(cardName);
    }
    displayPlayerHand();
    displayKitty();
  } else if(userLeading) {
    // user wants to play this card
    playUserCard(cardName);
  }
}

// Handle user clicking a kitty card
function handleKittyCardClick(cardName) {
  if(kittyRevealed) {
    // toggle
    if(selectedCards.includes(cardName)) {
      selectedCards = selectedCards.filter(c => c !== cardName);
    } else {
      selectedCards.push(cardName);
    }
    displayKitty();
    displayPlayerHand();
  }
}

function dataBackUrl(){
  return "https://deckofcardsapi.com/static/img/back.png";
}

function confirmKittyDiscard() {
  // The user picks which kitty cards to keep & which from their old hand to discard.
  // We'll do the simplest approach: the user selected them in 'selectedCards'.
  // So we must separate which are kitty vs. which are in-hand.
  let keepKitty = kittyCards.filter(k => selectedCards.includes(k.name)).map(k => k.name);
  // discard from the user's old hand
  let discardHand = yourCards.filter(y => selectedCards.includes(y.name)).map(y => y.name);
  let body = {
    keep_kitty_cards: keepKitty,
    discard_hand_cards: discardHand
  };
  fetch('/finalize_kitty', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })
  .then(r=>r.json())
  .then(data=>{
    log("Kitty Confirm: " + JSON.stringify(data));
    selectedCards = [];
    showState();
  });
}

function playUserCard(cardName) {
  fetch('/play_card_user', {
    method:'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({card_name: cardName})
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.error){
      log("Error: " + data.error);
    } else {
      log("Play Trick: " + data.message);
    }
    showState();
  });
}

function finalizeRound() {
  fetch('/finalize_round', {method:'POST'})
  .then(r=>r.json())
  .then(data=>{
    log("Finalize: " + JSON.stringify(data));
    showState();
  });
}
</script>

</body>
</html>
    """
    return html_content

###############################################################################
#                            API ROUTES                                       #
###############################################################################

@app.route("/new_round", methods=["POST"])
def new_round():
    global current_game, dealer_index, round_trick_count
    if not current_game:
        current_game = Game()
    else:
        current_game.reset_round_state()
    current_game.deal_hands(dealer_index)
    round_trick_count = 0
    return jsonify({"message":"new round dealt"})

@app.route("/bid", methods=["POST"])
def bid():
    global current_game, dealer_index
    data = request.get_json() or {}
    player_bid = data.get("player_bid", 0)
    current_game.perform_bidding(dealer_index, player_bid)
    winner_name = current_game.players[current_game.bid_winner].name
    return jsonify({"message": f"{winner_name} won the bid @ {current_game.bid}"})

@app.route("/select_trump", methods=["POST"])
def select_trump():
    global current_game
    if not current_game:
        return jsonify({"error":"no game in progress"}), 400
    data = request.get_json() or {}
    suit = data.get("suit")
    if suit not in ["Hearts","Diamonds","Clubs","Spades"]:
        return jsonify({"error":"invalid suit"}), 400
    current_game.set_trump_suit(suit)
    # If user is bidder, let's reveal kitty for selection
    if current_game.bid_winner == 0:  # user
        current_game.reveal_kitty_for_user_selection()
    else:  # computer
        current_game.computer_attach_kitty()
        current_game.allow_other_player_discard()
    return jsonify({"message": f"Trump set to {suit}"})

@app.route("/finalize_kitty", methods=["POST"])
def finalize_kitty():
    global current_game
    data = request.get_json() or {}
    keep_kitty = data.get("keep_kitty_cards", [])
    discard_hand = data.get("discard_hand_cards", [])
    current_game.finalize_kitty_selection(keep_kitty, discard_hand)
    # now allow other player to discard
    current_game.allow_other_player_discard()
    return jsonify({"message":"Kitty finalized"})

@app.route("/play_card_user", methods=["POST"])
def play_card_user():
    global current_game, round_trick_count
    data = request.get_json() or {}
    card_name = data.get("card_name")
    if not card_name:
        return jsonify({"error":"No card_name provided"}), 400
    result_msg = current_game.play_card_user(card_name)
    if result_msg.startswith("Error"):
        return jsonify({"error": result_msg}), 400
    round_trick_count += 1
    return jsonify({"message": result_msg})

@app.route("/finalize_round", methods=["POST"])
def finalize_round():
    global current_game, round_trick_count
    if not current_game:
        return jsonify({"error":"no game"}), 400
    if round_trick_count < 5:
        return jsonify({"error":"not all 5 tricks played"}), 400
    res = current_game.finalize_hand()
    return jsonify({
        "round_result": res,
        "scores": {
            "You": current_game.players[0].score,
            "Computer": current_game.players[1].score
        }
    })

@app.route("/show_state", methods=["GET"])
def show_state():
    global current_game, round_trick_count
    if not current_game:
        return jsonify({"error":"no game in progress"}),400

    user = current_game.players[0]
    comp = current_game.players[1]

    # Build a structured response for front-end:
    user_cards_info = [{
        "name": str(c),
        "img": card_to_image_url(str(c))
    } for c in user.hand]

    kitty_info = [{
        "name": str(c),
        "img": card_to_image_url(str(c))
    } for c in current_game.kitty]

    # last played cards: e.g. [("You", "5 of Hearts"), ("Computer", "K of Hearts")]
    # We'll attach the image URL as well for display
    played_cards_expanded = []
    for (pname, card_str) in current_game.last_played_cards:
        played_cards_expanded.append([pname, card_str, card_to_image_url(card_str)])

    # Are you the bid winner?
    user_is_bid_winner = (current_game.bid_winner == 0)

    # Are you leading right now?
    user_leading = (current_game.leading_player == 0)

    return jsonify({
        "your_cards": user_cards_info,
        "computer_count": len(comp.hand),
        "kitty": kitty_info,
        "kitty_revealed": current_game.kitty_revealed,
        "is_bid_winner": user_is_bid_winner,
        "kitty_attached": (not current_game.kitty_revealed and len(current_game.kitty)==0) if user_is_bid_winner else (current_game.bid_winner==1),
        "your_score": user.score,
        "computer_score": comp.score,
        "bid_winner": current_game.players[current_game.bid_winner].name if current_game.bid_winner is not None else None,
        "bid_amount": current_game.bid,
        "trump_suit": current_game.trump_suit,
        "tricks_played": round_trick_count,
        "user_leading": user_leading,
        "last_played_cards": played_cards_expanded,
        "trick_message": "",  # could store last trick message if you want
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
