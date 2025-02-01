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
    """
    Return the card's rank value for the given trump suit, or 0 if not found.
    """
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
#                  2) CARD IMAGE HELPERS (deckofcardsapi.com)                 #
###############################################################################

def card_to_image_url(card_str):
    """
    Convert "10 of Hearts" -> "https://deckofcardsapi.com/static/img/0H.png"
    Convert "A of Spades" -> ".../AS.png"
    etc.
    """
    # parse rank, suit
    # card_str e.g. "10 of Hearts"
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return "https://deckofcardsapi.com/static/img/back.png"  # fallback
    rank, suit = parts
    suit_letter = suit[0].upper()  # H, D, C, S

    # deckofcardsapi uses "0" for "10"
    if rank == "10":
        rank_code = "0"
    else:
        rank_code = rank.upper()[:1]  # e.g., "K", "Q", "A", "9", "2", etc.

    # Special case: "J", "Q", "K", "A" are single letters, but numeric ranks are as is
    # Actually "9 of Hearts" => "9H.png"
    # "A of Hearts" => "AH.png"
    # "10 of Hearts" => "0H.png"

    # If rank is "A", "J", "Q", "K", that's fine. If rank is "5", we do "5H".
    # So let's finalize:
    if rank_code in ["J", "Q", "K", "A", "0", "2", "3", "4", "5", "6", "7", "8", "9"]:
        pass
    else:
        # fallback if something else
        rank_code = rank[0].upper()  # just in case

    code = f"{rank_code}{suit_letter}"
    return f"https://deckofcardsapi.com/static/img/{code}.png"

def card_back_url():
    """URL for a card back image (computer's hand, kitty face-down, etc.)."""
    return "https://deckofcardsapi.com/static/img/back.png"

###############################################################################
#                  3) CLASSES (Card, Deck, Player, Game)                      #
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
        self.cards = []
        for s in suits:
            for r in ranks:
                self.cards.append(Card(s, r))
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

    def reset_round_state(self):
        self.deck = Deck()
        self.kitty.clear()
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card_played = None
        self.highest_card_owner = None
        for p in self.players:
            p.hand.clear()
            p.tricks_won = 0

    def deal_hands(self, dealer_index=1):
        self.deck.shuffle()
        for p in self.players:
            p.hand.clear()
        self.kitty.clear()

        eldest_index = 0 if dealer_index == 1 else 1
        # 3 each
        self.players[eldest_index].add_to_hand(self.deck.deal(3))
        self.players[dealer_index].add_to_hand(self.deck.deal(3))
        # kitty
        self.kitty.extend(self.deck.deal(3))
        # 2 each
        self.players[eldest_index].add_to_hand(self.deck.deal(2))
        self.players[dealer_index].add_to_hand(self.deck.deal(2))

    def perform_bidding(self, dealer_index=1, player_bid=0):
        comp_bid = random.choice([0, 15, 20, 25, 30])
        eldest_index = 0 if dealer_index == 1 else 1
        if eldest_index == 0:
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

    def attach_kitty(self):
        bidder = self.players[self.bid_winner]
        bidder.hand.extend(self.kitty)
        self.kitty.clear()
        # Simple discard logic
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
        for i, p in enumerate(self.players):
            if i == self.bid_winner:
                continue
            p.hand.sort(
                key=lambda c: get_card_rank(str(c), self.trump_suit),
                reverse=True
            )
            while len(p.hand) > 5:
                p.hand.pop()
            while len(p.hand) < 5 and len(self.deck.cards) > 0:
                p.hand.append(self.deck.deal(1)[0])

    def play_trick(self, lead_card_str=None):
        # Very naive logic for demonstration
        if lead_card_str is None and self.leading_player == 1:
            # Computer leads
            lead_card_str = self.computer_select_lead_card(self.players[1].hand)
            if not lead_card_str:
                return "Computer has no cards to lead."
            lead_card = next(c for c in self.players[1].hand if str(c) == lead_card_str)
            self.players[1].hand.remove(lead_card)
            trick_log = f"Computer led {lead_card_str}. "

            # Your auto-response (for demonstration, random)
            if self.players[0].hand:
                respond_card_str = random.choice([str(c) for c in self.players[0].hand])
                respond_card = next(c for c in self.players[0].hand if str(c) == respond_card_str)
                self.players[0].hand.remove(respond_card)
                trick_log += f"You played {respond_card_str}. "
            else:
                respond_card = None
                trick_log += "You have no cards left to play."

            winner_index = self.evaluate_trick_winner([(1, lead_card), (0, respond_card)] if respond_card else [(1, lead_card)])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            trick_log += f"Winner: {self.players[winner_index].name}."

            # Highest card check
            for pid, cobj in [(1, lead_card), (0, respond_card)]:
                if cobj:
                    val = get_card_rank(str(cobj), self.trump_suit)
                    if self.highest_card_played is None or val > get_card_rank(self.highest_card_played, self.trump_suit):
                        self.highest_card_played = str(cobj)
                        self.highest_card_owner = pid

            self.leading_player = winner_index
            return trick_log

        elif self.leading_player == 0:
            # You lead
            if lead_card_str not in [str(c) for c in self.players[0].hand]:
                return "User tried to lead a card not in hand."

            lead_card = next(c for c in self.players[0].hand if str(c) == lead_card_str)
            self.players[0].hand.remove(lead_card)
            trick_log = f"You led {lead_card_str}. "

            # Computer responds
            respond_card_str = self.computer_follow_card(self.players[1], lead_card.suit)
            comp_card = next(c for c in self.players[1].hand if str(c) == respond_card_str)
            self.players[1].hand.remove(comp_card)
            trick_log += f"Computer played {respond_card_str}. "

            winner_index = self.evaluate_trick_winner([(0, lead_card), (1, comp_card)])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            trick_log += f"Winner: {self.players[winner_index].name}."

            # Highest card check
            for pid, cobj in [(0, lead_card), (1, comp_card)]:
                val = get_card_rank(str(cobj), self.trump_suit)
                if self.highest_card_played is None or val > get_card_rank(self.highest_card_played, self.trump_suit):
                    self.highest_card_played = str(cobj)
                    self.highest_card_owner = pid

            self.leading_player = winner_index
            return trick_log
        else:
            return "Invalid play or missing 'lead_card' (user lead) if leading_player=0."

    def evaluate_trick_winner(self, played_cards):
        if not played_cards:
            return 0
        lead_suit = played_cards[0][1].suit
        trump_cards = []
        for pid, c in played_cards:
            rank_val = get_card_rank(str(c), self.trump_suit)
            if rank_val >= 100:
                trump_cards.append((pid, c))
        if trump_cards:
            winner_pid, winner_card = max(trump_cards, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
            return winner_pid
        else:
            same_suit = [(pid, c) for (pid, c) in played_cards if c and c.suit == lead_suit]
            if not same_suit:
                return played_cards[0][0]  # fallback
            winner_pid, winner_card = max(same_suit, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
            return winner_pid

    def computer_select_lead_card(self, comp_hand):
        if not comp_hand:
            return None
        comp_hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
        return str(comp_hand[0])

    def computer_follow_card(self, player_obj, lead_suit):
        # naive
        valid_cards = [c for c in player_obj.hand if c.suit == lead_suit]
        if valid_cards:
            valid_cards.sort(key=lambda x: get_card_rank(str(x), self.trump_suit), reverse=True)
            return str(valid_cards[0])
        else:
            player_obj.hand.sort(key=lambda x: get_card_rank(str(x), self.trump_suit))
            return str(player_obj.hand[-1])

    def finalize_hand(self):
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5

        bidder = self.players[self.bid_winner]
        bidder_points_this_round = bidder.tricks_won * 5
        if self.highest_card_owner == self.bid_winner:
            bidder_points_this_round += 5
        if bidder_points_this_round < self.bid:
            bidder.score -= self.bid

        result = {"game_over": False, "winner": None}
        p0 = self.players[0].score
        p1 = self.players[1].score
        if p0 >= 120 and p1 >= 120:
            result["game_over"] = True
            result["winner"] = self.players[self.bid_winner].name
        elif p0 >= 120:
            result["game_over"] = True
            result["winner"] = self.players[0].name
        elif p1 >= 120:
            result["game_over"] = True
            result["winner"] = self.players[1].name
        return result

###############################################################################
#                   4) GLOBALS & FLASK ROUTES (WITH UI)                       #
###############################################################################

current_game = None
dealer_index = 1
round_trick_count = 0

@app.route("/", methods=["GET"])
def index():
    """
    Returns a simple HTML + JS page. We also display the kitty, computer's hand as face-down images,
    and your hand face-up.
    """
    html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>Forty-Fives with Card Images</title>
    <style>
      body { font-family: sans-serif; }
      #log { white-space: pre-wrap; background: #f8f8f8; padding: 10px; margin-top: 10px; }
      .card-row { display: flex; flex-wrap: wrap; margin: 5px 0; }
      .card { margin: 2px; }
    </style>
</head>
<body>
<h1>Heads-Up Forty-Fives (120 pts) - Card Images</h1>
<div>
  <button onclick="newRound()">New Round</button>
  <button onclick="showState()">Show State</button>
</div>
<div>
  <label>Bid:</label>
  <select id="bidVal">
    <option value="0">Pass</option>
    <option value="15">15</option>
    <option value="20">20</option>
    <option value="25">25</option>
    <option value="30">30</option>
  </select>
  <button onclick="placeBid()">Place Bid</button>
</div>
<div>
  <label>Trump Suit:</label>
  <select id="trumpSuit">
    <option>Hearts</option>
    <option>Diamonds</option>
    <option>Clubs</option>
    <option>Spades</option>
  </select>
  <button onclick="chooseTrump()">Select Trump</button>
</div>
<div>
  <button onclick="attachKitty()">Attach Kitty</button>
</div>
<div>
  <label>Your lead card:</label>
  <input type="text" id="leadCard" placeholder="e.g. 'K of Hearts'">
  <button onclick="playTrick()">Play Trick</button>
</div>
<div>
  <button onclick="finalizeRound()">Finalize Round</button>
</div>

<h2>Game State</h2>
<div id="scores"></div>
<div>
  <h3>Your Hand</h3>
  <div id="playerHand" class="card-row"></div>
  <h3>Computer's Hand (Face-Down)</h3>
  <div id="computerHand" class="card-row"></div>
  <h3>Kitty</h3>
  <div id="kittyCards" class="card-row"></div>
</div>
<pre id="log"></pre>

<script>
async function newRound() {
  const resp = await fetch('/new_round', { method: 'POST' });
  const data = await resp.json();
  log("New Round: " + JSON.stringify(data, null, 2));
  showState();
}

async function showState() {
  const resp = await fetch('/show_state');
  const data = await resp.json();
  if (data.error) { log("Error: " + data.error); return; }

  // Update scores
  let scoresDiv = document.getElementById('scores');
  scoresDiv.innerHTML = "You: " + data.player_score + " | Computer: " + data.computer_score +
    "<br>Bid winner: " + data.bid_winner + " (bid=" + data.bid + "), Trump: " + (data.trump_suit || "(none)") +
    "<br>Tricks played: " + data.tricks_played;

  // Player hand (face-up)
  let playerDiv = document.getElementById('playerHand');
  playerDiv.innerHTML = "";
  if (data.player_hand_images) {
    data.player_hand_images.forEach(url => {
      playerDiv.innerHTML += '<img class="card" src="'+ url +'" height="120">';
    });
  }

  // Computer hand (face-down)
  let compDiv = document.getElementById('computerHand');
  compDiv.innerHTML = "";
  for (let i = 0; i < data.computer_hand_count; i++) {
    compDiv.innerHTML += '<img class="card" src="' + data.card_back + '" height="120">';
  }

  // Kitty (face-down if not attached, otherwise face-up for demonstration)
  let kittyDiv = document.getElementById('kittyCards');
  kittyDiv.innerHTML = "";
  if (!data.kitty_attached) {
    // show them face-down
    for (let i = 0; i < data.kitty_size; i++) {
      kittyDiv.innerHTML += '<img class="card" src="' + data.card_back + '" height="120">';
    }
  } else {
    // show them face-up (the code auto-discards, so these might be fewer or none)
    if (data.kitty_images && data.kitty_images.length > 0) {
      data.kitty_images.forEach(url => {
        kittyDiv.innerHTML += '<img class="card" src="'+ url +'" height="120">';
      });
    }
  }
}

async function placeBid() {
  let val = parseInt(document.getElementById('bidVal').value);
  const resp = await fetch('/bid', {
    method: 'POST',
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ player_bid: val })
  });
  const data = await resp.json();
  log("Bid: " + JSON.stringify(data, null, 2));
  showState();
}

async function chooseTrump() {
  let suit = document.getElementById('trumpSuit').value;
  const resp = await fetch('/select_trump', {
    method: 'POST',
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ suit })
  });
  const data = await resp.json();
  log("Set Trump: " + JSON.stringify(data, null, 2));
  showState();
}

async function attachKitty() {
  const resp = await fetch('/attach_kitty', { method: 'POST' });
  const data = await resp.json();
  log("Attach Kitty: " + JSON.stringify(data, null, 2));
  showState();
}

async function playTrick() {
  let cardInput = document.getElementById('leadCard').value.trim();
  if (!cardInput) cardInput = null;
  const bodyObj = cardInput ? { lead_card: cardInput } : {};
  const resp = await fetch('/play_trick', {
    method: 'POST',
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(bodyObj)
  });
  const data = await resp.json();
  if (data.error) {
    log("Error: " + data.error);
  } else {
    if (data.trick_result) {
      log("Trick: " + data.trick_result);
    } else {
      log(JSON.stringify(data, null, 2));
    }
  }
  showState();
}

async function finalizeRound() {
  const resp = await fetch('/finalize_round', { method: 'POST' });
  const data = await resp.json();
  log("Finalize: " + JSON.stringify(data, null, 2));
  showState();
}

function log(msg) {
  document.getElementById('log').textContent += msg + "\\n";
}
</script>

</body>
</html>
    """
    return html_page

###############################################################################
#                            5) FLASK API ROUTES                              #
###############################################################################

@app.route("/new_round", methods=["POST"])
def new_round():
    global current_game, dealer_index, round_trick_count
    if current_game is None:
        current_game = Game()
    else:
        current_game.reset_round_state()
    current_game.deal_hands(dealer_index)
    round_trick_count = 0
    return jsonify({"message": "New round dealt."})

@app.route("/bid", methods=["POST"])
def bid():
    global current_game, dealer_index
    if not current_game:
        return jsonify({"error": "No game in progress"}), 400
    data = request.get_json() or {}
    player_bid = data.get("player_bid", 0)
    current_game.perform_bidding(dealer_index, player_bid)
    winner = current_game.players[current_game.bid_winner].name
    return jsonify({"message": f"{winner} won the bid with {current_game.bid}."})

@app.route("/select_trump", methods=["POST"])
def select_trump():
    global current_game
    if not current_game:
        return jsonify({"error": "No game in progress"}), 400
    if current_game.bid_winner is None:
        return jsonify({"error": "No bid winner yet."}), 400
    data = request.get_json() or {}
    suit = data.get("suit")
    if suit not in ["Hearts", "Diamonds", "Clubs", "Spades"]:
        return jsonify({"error": "Invalid suit."}), 400
    current_game.set_trump_suit(suit)
    return jsonify({"message": f"Trump set to {suit}."})

@app.route("/attach_kitty", methods=["POST"])
def attach_kitty():
    global current_game
    if not current_game:
        return jsonify({"error": "No game in progress"}), 400
    if current_game.bid_winner is None:
        return jsonify({"error": "No bid winner yet."}), 400
    if current_game.trump_suit is None:
        return jsonify({"error": "No trump suit set yet."}), 400

    current_game.attach_kitty()
    current_game.allow_other_player_discard()
    return jsonify({"message": "Kitty attached and discard done."})

@app.route("/play_trick", methods=["POST"])
def play_trick():
    global current_game, round_trick_count
    if not current_game:
        return jsonify({"error": "No game in progress"}), 400
    data = request.get_json() or {}
    lead_card_str = data.get("lead_card")
    result = current_game.play_trick(lead_card_str)
    if "error" in result.lower():
        return jsonify({"error": result})
    round_trick_count += 1
    return jsonify({"trick_result": result})

@app.route("/finalize_round", methods=["POST"])
def finalize_round():
    global current_game, round_trick_count
    if not current_game:
        return jsonify({"error": "No game in progress"}), 400
    if round_trick_count < 5:
        return jsonify({"error": "Not all 5 tricks have been played."}), 400
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
        return jsonify({"error": "No game in progress"}), 400

    # Build data for player's hand (face-up):
    player_hand = current_game.players[0].hand
    player_hand_images = [card_to_image_url(str(c)) for c in player_hand]

    # Computer's hand size (face-down):
    comp_count = len(current_game.players[1].hand)

    # For demonstration, if the kitty isn't attached, show them as face-down. If attached, show them face-up.
    kitty_size = len(current_game.kitty)
    kitty_images = [card_to_image_url(str(c)) for c in current_game.kitty]

    # Are we sure the kitty is "attached"? i.e. has the bidder taken it yet?
    # In this code, once the bidder attaches the kitty, we empty self.kitty, but we do it
    # after discarding. Actually, we just appended them to the bidder. So let's do:
    kitty_attached = (current_game.bid_winner is not None and kitty_size < 3)

    return jsonify({
        "player_score": current_game.players[0].score,
        "computer_score": current_game.players[1].score,
        "player_hand_images": player_hand_images,
        "computer_hand_count": comp_count,
        "kitty_size": kitty_size,
        "kitty_images": kitty_images,  # face-up images
        "kitty_attached": kitty_attached,
        "bid_winner": current_game.bid_winner,
        "bid": current_game.bid,
        "trump_suit": current_game.trump_suit,
        "tricks_played": round_trick_count,
        "card_back": card_back_url()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
