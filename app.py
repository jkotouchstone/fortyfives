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
    """Return a numeric rank for `card_str` under `trump_suit`."""
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
    """URL for a card back image."""
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    """
    Convert '10 of Hearts' => 'https://deckofcardsapi.com/static/img/0H.png'
    """
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return card_back_url()
    rank, suit = parts
    suit_letter = suit[0].upper()
    rank_code = "0" if rank == "10" else rank.upper()[0]
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
        self.round_score = 0
        self.tricks_won = 0
    def add_to_hand(self, cards):
        self.hand.extend(cards)

class Game:
    def __init__(self):
        self.players = [Player("You"), Player("Computer")]
        self.dealer = 1  # 0=You, 1=Computer
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card_played = None
        self.highest_card_owner = None
        self.last_played_cards = []
        self.kitty_revealed = False

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
            p.round_score = 0

    def rotate_dealer(self):
        self.dealer = 1 - self.dealer

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand.clear()
        self.kitty.clear()
        first_bidder = 0 if self.dealer == 1 else 1
        # 3 each, 3 kitty, then 2 each
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def perform_bidding(self, player_bid):
        """
        If you are not the dealer, you bid first, then the dealer (possibly the computer) bids.
        """
        first_bidder = 0 if self.dealer == 1 else 1
        if first_bidder == 0:
            # you first
            your_bid = player_bid
            comp_bid = random.choice([0, 15, 20, 25, 30])
            if your_bid > comp_bid:
                self.bid_winner = 0
                self.bid = your_bid
            else:
                self.bid_winner = 1
                self.bid = comp_bid if comp_bid>0 else 15
        else:
            # computer first
            comp_bid = random.choice([0, 15, 20, 25, 30])
            your_bid = player_bid
            if comp_bid > your_bid:
                self.bid_winner = 0
                self.bid = comp_bid
            else:
                self.bid_winner = 1
                self.bid = your_bid if your_bid>0 else 15

    def set_trump(self, suit=None):
        if self.bid_winner == 1 and self.dealer == 1:
            # computer picks automatically
            comp_hand = self.players[1].hand
            suit_counts = {"Hearts":0, "Diamonds":0, "Clubs":0, "Spades":0}
            for c in comp_hand:
                suit_counts[c.suit]+=1
            self.trump_suit = max(suit_counts, key=suit_counts.get)
        else:
            self.trump_suit = suit

    def attach_kitty(self):
        if self.bid_winner == 1:
            # computer
            comp = self.players[1]
            comp.add_to_hand(self.kitty)
            self.kitty.clear()
            def keep(c):
                return (c.suit==self.trump_suit) or (c.suit=="Hearts" and c.rank=="A")
            comp.hand.sort(key=lambda x: (keep(x), get_card_rank(str(x), self.trump_suit)), reverse=True)
            while len(comp.hand)>5:
                comp.hand.pop()
        else:
            self.kitty_revealed = True

    def finalize_kitty_selection(self, keep_from_kitty, discard_from_hand):
        # user is bidder
        user = self.players[0]
        user.hand = [c for c in user.hand if str(c) not in discard_from_hand]
        kitty_to_keep = []
        kitty_leftover = []
        for c in self.kitty:
            if str(c) in keep_from_kitty:
                kitty_to_keep.append(c)
            else:
                kitty_leftover.append(c)
        user.hand.extend(kitty_to_keep)
        self.kitty = kitty_leftover
        self.kitty_revealed = False

        # if >5, discard extras
        discards = []
        while len(user.hand)>5:
            discards.append(str(user.hand.pop()))
        new_cards = self.deck.deal(len(discards))
        user.hand.extend(new_cards)

        return {"discarded": discards, "drawn": [str(c) for c in new_cards]}

    def play_trick_user(self, card_str):
        user = self.players[0]
        if card_str not in [str(c) for c in user.hand]:
            return "Error: Card not in hand."
        played_card = next(c for c in user.hand if str(c) == card_str)
        user.hand.remove(played_card)

        self.last_played_cards = [(user.name, str(played_card), card_to_image_url(str(played_card)))]
        if self.leading_player == 0:
            # you lead
            comp = self.players[1]
            follow = self.computer_select_follow(comp, played_card.suit)
            comp.hand.remove(follow)
            self.last_played_cards.append((comp.name, str(follow), card_to_image_url(str(follow))))
            winner = self.evaluate_trick([(0, played_card), (1, follow)])
        else:
            # computer leads
            comp = self.players[1]
            lead = self.computer_select_lead(comp.hand)
            comp.hand.remove(lead)
            self.last_played_cards = [
                (comp.name, str(lead), card_to_image_url(str(lead))),
                (user.name, str(played_card), card_to_image_url(str(played_card)))
            ]
            winner = self.evaluate_trick([(1, lead), (0, played_card)])

        self.players[winner].score += 5
        self.players[winner].tricks_won += 1
        self.leading_player = winner
        return f"Trick played. Winner: {self.players[winner].name}"

    def computer_select_lead(self, hand):
        hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
        return hand[0] if hand else None

    def computer_select_follow(self, comp, lead_suit):
        valid = [c for c in comp.hand if c.suit==lead_suit]
        if valid:
            valid.sort(key=lambda c: get_card_rank(str(c), self.trump_suit))
            return valid[0]
        else:
            comp.hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit))
            return comp.hand[0]

    def evaluate_trick(self, plays):
        lead_suit = plays[0][1].suit
        trump_plays = [(i, c) for (i, c) in plays if get_card_rank(str(c), self.trump_suit)>=100]
        if trump_plays:
            (win_pid, win_card) = max(trump_plays, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
        else:
            same_suit = [(i, c) for (i, c) in plays if c.suit==lead_suit]
            (win_pid, win_card) = max(same_suit, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
        # track highest
        val = get_card_rank(str(win_card), self.trump_suit)
        if self.highest_card_played is None or val>get_card_rank(self.highest_card_played, self.trump_suit):
            self.highest_card_played = str(win_card)
            self.highest_card_owner = win_pid
        return win_pid

    def finalize_round(self):
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5
        round_scores = [p.tricks_won*5 for p in self.players]
        if round_scores[self.bid_winner] < self.bid:
            self.players[self.bid_winner].score -= self.bid
            round_scores[self.bid_winner] = -self.bid
        return {"round_scores": round_scores,
                "total_scores": [self.players[0].score, self.players[1].score]}

###############################################################################
#                 4) FLASK GLOBALS & ROUTES (Interactive UI)                 #
###############################################################################
current_game = None
round_tricks = 0

@app.route("/", methods=["GET"])
def index():
    """
    The main HTML page with no popup alerts, slightly adjusted layout.
    """
    html = """
<!DOCTYPE html>
<html>
<head>
  <title>Forty-Fives - Card Table</title>
  <style>
    body { margin: 0; padding: 0; background-color: darkgreen; font-family: Arial, sans-serif; color: white; }
    #table { position: relative; width: 100%; height: 100vh; }
    #controls {
      position: absolute; top: 0; left: 0; width: 100%; text-align: center;
      padding: 10px; background: rgba(0,0,0,0.5);
    }
    #computerArea {
      position: absolute;
      top: 80px; /* Moved down so it doesn't overlap #controls */
      left: 50%;
      transform: translateX(-50%);
      text-align: center;
    }
    #playerArea {
      position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); text-align: center;
    }
    #kittyArea {
      position: absolute; left: 20px; top: 50%; transform: translateY(-50%); text-align: center;
    }
    #deckArea {
      position: absolute; right: 20px; top: 50%; transform: translateY(-50%); text-align: center;
    }
    #centerArea {
      position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
      text-align: center;
    }
    #scoreboard {
      position: absolute; bottom: 0; right: 0;
      background: rgba(255,255,255,0.8); color: black;
      padding: 10px; margin: 10px; border-radius: 5px;
    }
    .card { width: 80px; margin: 5px; border-radius: 5px; cursor: pointer; }
    .selected { outline: 3px solid yellow; }
    button { margin: 5px; padding: 5px 10px; border-radius: 4px; border: none; background: #555; color: #fff; cursor: pointer; }
    button:hover { background: #666; }
    .hidden { display: none; }
    #logArea {
      position: absolute; left: 50%; top: 60%; transform: translate(-50%,0);
      width: 500px; max-height: 150px; overflow-y: auto; background: rgba(0,0,0,0.3); padding:10px;
    }
  </style>
</head>
<body>
<div id="table">
  <div id="controls">
    <button onclick="rotateDealer()">Rotate Dealer</button>
    <span id="dealerLabel"></span>
    <button onclick="newRound()">New Round</button>
    <button onclick="showState()">Refresh</button>
    <button onclick="finalizeRound()">Finalize Round</button>
    <br>
    <label id="bidLabel"></label>
    <button onclick="startBid()">Start Bid</button>
    <div id="bidControls" class="hidden">
      <label>Your Bid:</label>
      <select id="bidValue">
        <option value="15">15</option>
        <option value="20">20</option>
        <option value="25">25</option>
        <option value="30">30</option>
        <option value="0">Pass</option>
      </select>
      <button onclick="submitBid()">Submit Bid</button>
    </div>
    <div id="trumpControls" class="hidden">
      <label>Select Trump:</label>
      <select id="trumpValue">
        <option>Hearts</option>
        <option>Diamonds</option>
        <option>Clubs</option>
        <option>Spades</option>
      </select>
      <button onclick="submitTrump()">Submit Trump</button>
    </div>
  </div>

  <div id="computerArea">
    <h3>Computer's Hand</h3>
    <div id="computerHand"></div>
  </div>

  <div id="kittyArea">
    <h3>Kitty</h3>
    <div id="kittyDisplay"></div>
    <button id="confirmKittyBtn" class="hidden" onclick="confirmKitty()">Confirm Kitty Selection</button>
  </div>

  <div id="deckArea">
    <h3>Deck</h3>
    <img id="deckImg" class="card" src="" alt="Deck">
    <div id="deckCount"></div>
  </div>

  <div id="centerArea">
    <h3>Current Trick</h3>
    <div id="trickArea"></div>
  </div>

  <div id="playerArea">
    <h3>Your Hand</h3>
    <div id="playerHand"></div>
  </div>

  <div id="scoreboard">
    <h3>Score Notebook</h3>
    <div id="scoreInfo"></div>
  </div>

  <!-- This is a simple log area for messages (replacing popups) -->
  <div id="logArea"></div>
</div>

<script>
let selectedKitty = [];
let selectedDiscards = [];
let gameState = {};

function log(msg) {
  const logDiv = document.getElementById('logArea');
  const p = document.createElement('p');
  p.textContent = msg;
  logDiv.appendChild(p);
  logDiv.scrollTop = logDiv.scrollHeight;
}

function rotateDealer() {
  fetch('/rotate_dealer')
    .then(r => r.json())
    .then(data => {
      log("Dealer rotated to: " + data.dealer);
      showState();
    });
}

function newRound() {
  fetch('/new_round', {method:'POST'})
    .then(r => r.json())
    .then(data => {
      log(data.message);
      showState();
    });
}

function startBid() {
  document.getElementById('bidControls').classList.remove('hidden');
}

function submitBid() {
  let bidVal = parseInt(document.getElementById('bidValue').value);
  fetch('/bid', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({player_bid: bidVal})
  })
  .then(r => r.json())
  .then(data => {
    log(data.message);
    showState();
  });
}

function submitTrump() {
  let trump = document.getElementById('trumpValue').value;
  fetch('/select_trump', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({suit: trump})
  })
  .then(r=>r.json())
  .then(data => {
    log(data.message);
    showState();
  });
}

function confirmKitty() {
  fetch('/finalize_kitty', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({keep: selectedKitty, discard: selectedDiscards})
  })
  .then(r => r.json())
  .then(resp => {
    log(resp.message);
    selectedKitty = [];
    selectedDiscards = [];
    showState();
  });
}

function playCard(cardName) {
  fetch('/play_card_user', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({card_name: cardName})
  })
  .then(r=>r.json())
  .then(data => {
    log(data.message);
    showState();
  });
}

function finalizeRound() {
  fetch('/finalize_round', {method:'POST'})
    .then(r => r.json())
    .then(data => {
      if(data.error) {
        log(data.error);
      } else {
        log("Round finalized. " + JSON.stringify(data));
      }
      showState();
    });
}

function showState() {
  fetch('/show_state')
  .then(r => r.json())
  .then(data => {
    if(data.error) {
      log(data.error);
      return;
    }
    gameState = data;
    updateDealerLabel(data.dealer);
    updateHands(data);
    updateKitty(data);
    updateDeck(data);
    updateTrick(data);
    updateScoreboard(data);

    document.getElementById('bidControls').classList.toggle('hidden', data.bid_submitted);
    document.getElementById('trumpControls').classList.toggle('hidden', data.trump_set);
    document.getElementById('confirmKittyBtn').classList.toggle('hidden', !data.show_kitty_confirm);
  });
}

function updateDealerLabel(dealer) {
  document.getElementById('dealerLabel').innerText = "Dealer: " + dealer;
}

function updateHands(data) {
  let ph = document.getElementById('playerHand');
  ph.innerHTML = "";
  data.your_cards.forEach(card => {
    let img = document.createElement('img');
    img.src = card.img;
    img.className = "card";
    img.onclick = () => playCard(card.name);
    ph.appendChild(img);
  });

  let ch = document.getElementById('computerHand');
  ch.innerHTML = "";
  for(let i=0; i<data.computer_count; i++) {
    let img = document.createElement('img');
    img.src = data.card_back;
    img.className = "card";
    ch.appendChild(img);
  }
}

function updateKitty(data) {
  let kd = document.getElementById('kittyDisplay');
  kd.innerHTML = "";
  if(data.kitty_revealed) {
    data.kitty.forEach(card => {
      let img = document.createElement('img');
      img.src = card.img;
      img.className = "card";
      img.onclick = () => {
        if(selectedKitty.includes(card.name)) {
          selectedKitty = selectedKitty.filter(x=>x!==card.name);
        } else {
          selectedKitty.push(card.name);
        }
        updateKitty(data);
      };
      if(selectedKitty.includes(card.name)) {
        img.classList.add('selected');
      }
      kd.appendChild(img);
    });
  } else {
    for(let i=0; i<data.kitty.length; i++){
      let img = document.createElement('img');
      img.src = data.card_back;
      img.className = "card";
      kd.appendChild(img);
    }
  }
}

function updateDeck(data) {
  document.getElementById('deckImg').src = data.card_back;
  document.getElementById('deckCount').innerText = "Remaining: " + data.deck_count;
}

function updateTrick(data) {
  let t = document.getElementById('trickArea');
  t.innerHTML = "";
  if(data.last_trick && data.last_trick.length>0) {
    data.last_trick.forEach(item => {
      let [pname, cardstr, imgUrl] = item;
      let img = document.createElement('img');
      img.src = imgUrl;
      img.className = "card";
      t.appendChild(img);
    });
  }
}

function updateScoreboard(data) {
  let s = document.getElementById('scoreInfo');
  s.innerHTML = `Round Score - You: ${data.round_score_your}, Computer: ${data.round_score_comp}<br>
  Total: You ${data.total_your} / Computer ${data.total_comp}`;
}
</script>
</body>
</html>
    """
    return html

###############################################################################
#                            5) FLASK API ROUTES                              #
###############################################################################

@app.route("/rotate_dealer", methods=["GET"])
def rotate_dealer():
    global current_game
    if current_game:
        current_game.rotate_dealer()
        return jsonify({"dealer": current_game.players[current_game.dealer].name})
    return jsonify({"error": "No game in progress"}), 400

current_game = None
round_tricks = 0

@app.route("/new_round", methods=["POST"])
def new_round_api():
    global current_game, round_tricks
    if not current_game:
        current_game = Game()
    else:
        current_game.reset_round_state()
    current_game.deal_hands()
    round_tricks = 0
    return jsonify({"message": "New round dealt"})

@app.route("/bid", methods=["POST"])
def bid_api():
    global current_game
    data = request.get_json() or {}
    player_bid = data.get("player_bid", 0)
    current_game.perform_bidding(player_bid)
    msg = f"{current_game.players[current_game.bid_winner].name} won the bid at {current_game.bid}"
    return jsonify({"message": msg})

@app.route("/select_trump", methods=["POST"])
def select_trump_api():
    global current_game
    data = request.get_json() or {}
    if current_game.bid_winner == 0:
        suit = data.get("suit")
        if suit not in ["Hearts","Diamonds","Clubs","Spades"]:
            return jsonify({"error":"Invalid suit"}), 400
        current_game.set_trump(suit)
    else:
        current_game.set_trump()
    if current_game.bid_winner == 1:
        current_game.attach_kitty()
    else:
        current_game.kitty_revealed = True
    return jsonify({"message": f"Trump set to {current_game.trump_suit}"})

@app.route("/finalize_kitty", methods=["POST"])
def finalize_kitty_api():
    global current_game
    data = request.get_json() or {}
    keep = data.get("keep", [])
    discard = data.get("discard", [])
    result = current_game.finalize_kitty_selection(keep, discard)
    return jsonify({"message": "Kitty finalized", "discard_info": result})

@app.route("/play_card_user", methods=["POST"])
def play_card_user_api():
    global current_game, round_tricks
    data = request.get_json() or {}
    card_name = data.get("card_name")
    if not card_name:
        return jsonify({"error":"No card provided"}), 400
    outcome = current_game.play_trick_user(card_name)
    if not outcome.startswith("Error"):
        round_tricks += 1
    return jsonify({"message": outcome})

@app.route("/finalize_round", methods=["POST"])
def finalize_round_api():
    global current_game, round_tricks
    if round_tricks < 5:
        return jsonify({"error":"Not all 5 tricks played"}), 400
    res = current_game.finalize_round()
    return jsonify({"round_result": res})

@app.route("/show_state", methods=["GET"])
def show_state_api():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}), 400
    
    user = current_game.players[0]
    comp = current_game.players[1]
    
    your_cards_list = [{"name":str(c),"img":card_to_image_url(str(c))} for c in user.hand]
    kitty_list = [{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]

    state = {
        "your_cards": your_cards_list,
        "computer_count": len(comp.hand),
        "kitty": kitty_list,
        "kitty_revealed": current_game.kitty_revealed,
        "bid_winner": current_game.players[current_game.bid_winner].name if current_game.bid_winner is not None else None,
        "bid": current_game.bid,
        "trump_suit": current_game.trump_suit,
        "deck_count": len(current_game.deck.cards),
        "card_back": card_back_url(),
        "last_trick": current_game.last_played_cards,
        "dealer": current_game.players[current_game.dealer].name,
        "bid_submitted": (current_game.bid>0),
        "trump_set": (current_game.trump_suit is not None),
        "show_kitty_confirm": (current_game.bid_winner==0 and current_game.kitty_revealed),
        "round_score_your": user.tricks_won*5,
        "round_score_comp": comp.tricks_won*5,
        "total_your": user.score,
        "total_comp": comp.score
    }
    return jsonify(state)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
