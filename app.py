import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                                  RANK TABLES                                #
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
#                                GAME CLASSES                                 #
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

###############################################################################
#                             MAIN GAME LOGIC                                 #
###############################################################################

class Game:
    def __init__(self):
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # index 0 or 1
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

        # Eldest = 0 if dealer=1
        eldest_index = 0 if dealer_index == 1 else 1

        # 3 each
        self.players[eldest_index].add_to_hand(self.deck.deal(3))
        self.players[dealer_index].add_to_hand(self.deck.deal(3))

        # kitty 3
        self.kitty.extend(self.deck.deal(3))

        # 2 each
        self.players[eldest_index].add_to_hand(self.deck.deal(2))
        self.players[dealer_index].add_to_hand(self.deck.deal(2))

    def get_player_hand_strings(self, player_index=0):
        return [str(c) for c in self.players[player_index].hand]

    def perform_bidding(self, dealer_index=1, player_bid=0):
        # naive computer bid
        comp_bid = random.choice([0, 15, 20, 25, 30])

        eldest_index = 0 if dealer_index == 1 else 1
        if eldest_index == 0:
            p0_bid = player_bid
            p1_bid = comp_bid
        else:
            p0_bid = comp_bid
            p1_bid = player_bid

        # if both pass => dealer forced to 15
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
        if lead_card_str is None and self.leading_player == 1:
            # computer leads
            lead_card_str = self.computer_select_lead_card(self.players[1].hand)
            lead_card = next(c for c in self.players[1].hand if str(c) == lead_card_str)
            self.players[1].hand.remove(lead_card)
            trick_log = f"Computer led {lead_card_str}. "

            # user auto-respond?? Here we can’t auto-pick user’s card. We’ll skip a real follow-suit check for demonstration.
            # In a real interactive UI, the user must pick. Let's do the simplest: user picks random:
            if self.players[0].hand:
                respond_card_str = random.choice([str(c) for c in self.players[0].hand])
                respond_card = next(c for c in self.players[0].hand if str(c) == respond_card_str)
                self.players[0].hand.remove(respond_card)
                trick_log += f"You played {respond_card_str}. "
            else:
                respond_card = None
                trick_log += "You have no cards left to play. "

            winner_index = self.evaluate_trick_winner([(1, lead_card), (0, respond_card)] if respond_card else [(1, lead_card)])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            trick_log += f"Winner: {self.players[winner_index].name}."

            # highest card check
            for pid, cobj in [(1, lead_card), (0, respond_card)]:
                if cobj:
                    val = get_card_rank(str(cobj), self.trump_suit)
                    if self.highest_card_played is None or val > get_card_rank(self.highest_card_played, self.trump_suit):
                        self.highest_card_played = str(cobj)
                        self.highest_card_owner = pid

            self.leading_player = winner_index
            return trick_log

        elif self.leading_player == 0:
            # user leads
            if lead_card_str not in [str(c) for c in self.players[0].hand]:
                return "User tried to lead a card not in hand."

            lead_card = next(c for c in self.players[0].hand if str(c) == lead_card_str)
            self.players[0].hand.remove(lead_card)
            trick_log = f"You led {lead_card_str}. "

            # computer responds
            comp_respond_str = self.computer_follow_card(self.players[1], lead_card.suit)
            comp_card = next(c for c in self.players[1].hand if str(c) == comp_respond_str)
            self.players[1].hand.remove(comp_card)
            trick_log += f"Computer played {comp_respond_str}. "

            winner_index = self.evaluate_trick_winner([(0, lead_card), (1, comp_card)])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            trick_log += f"Winner: {self.players[winner_index].name}."

            # highest card check
            for pid, cobj in [(0, lead_card), (1, comp_card)]:
                val = get_card_rank(str(cobj), self.trump_suit)
                if self.highest_card_played is None or val > get_card_rank(self.highest_card_played, self.trump_suit):
                    self.highest_card_played = str(cobj)
                    self.highest_card_owner = pid

            self.leading_player = winner_index
            return trick_log
        else:
            return "Invalid play. Possibly missing 'lead_card' or it's not your turn."

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
            same_suit = [(pid, c) for (pid, c) in played_cards if c.suit == lead_suit]
            winner_pid, winner_card = max(same_suit, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
            return winner_pid

    def computer_select_lead_card(self, comp_hand):
        comp_hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
        return str(comp_hand[0]) if comp_hand else None

    def computer_follow_card(self, player_obj, lead_suit):
        # super naive
        valid_cards = [c for c in player_obj.hand if c.suit == lead_suit]
        if valid_cards:
            valid_cards.sort(key=lambda x: get_card_rank(str(x), self.trump_suit), reverse=True)
            return str(valid_cards[0])
        else:
            player_obj.hand.sort(key=lambda x: get_card_rank(str(x), self.trump_suit))
            return str(player_obj.hand[-1])  # slough lowest

    def finalize_hand(self):
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5

        bidder = self.players[self.bid_winner]
        bidder_points_this_round = bidder.tricks_won * 5
        if self.highest_card_owner == self.bid_winner:
            bidder_points_this_round += 5

        if bidder_points_this_round < self.bid:
            bidder.score -= self.bid

        # check for 120
        result = {"game_over": False, "winner": None}
        p0 = self.players[0].score
        p1 = self.players[1].score
        if p0 >= 120 and p1 >= 120:
            # bidder goes out
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
#                               GLOBAL STATE                                  #
###############################################################################
current_game = None
dealer_index = 1  # let's fix the dealer as "Computer"
round_trick_count = 0

###############################################################################
#                             HTML + JS INTERFACE                             #
###############################################################################

@app.route("/", methods=["GET"])
def index():
    """
    Returns a simple HTML page with embedded JavaScript that allows
    you to play the game by clicking buttons. We’ll interact with the
    endpoints below.
    """
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Forty-Fives (Heads-Up)</title>
    <style>
      body { font-family: sans-serif; margin: 20px; }
      button { margin: 5px; }
      #log { white-space: pre-wrap; background: #f8f8f8; padding: 10px; margin-top: 10px; }
      #playerHand { margin-top: 10px; }
      .card { display: inline-block; padding: 8px; margin: 3px; background: #eee; border-radius: 5px; }
    </style>
</head>
<body>
<h1>Heads-Up Forty-Fives (120-Point)</h1>
<div>
  <button onclick="newRound()">New Round</button>
  <button onclick="showState()">Show State</button>
</div>
<div>
  <label>Bid Amount:</label>
  <select id="bidValue">
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
    <option value="Hearts">Hearts</option>
    <option value="Diamonds">Diamonds</option>
    <option value="Clubs">Clubs</option>
    <option value="Spades">Spades</option>
  </select>
  <button onclick="selectTrump()">Select Trump</button>
</div>
<div>
  <button onclick="attachKitty()">Attach Kitty</button>
  <button onclick="playTrick()">Play Trick</button>
  <label>(If it's your lead, specify card:)</label>
  <input id="leadCard" type="text" placeholder="e.g. 'K of Clubs'">
</div>
<div>
  <button onclick="finalizeRound()">Finalize Round</button>
</div>

<hr>
<div id="playerHand"></div>
<div id="scores"></div>
<pre id="log"></pre>

<script>
async function newRound() {
  const resp = await fetch('/new_round', { method: 'POST' });
  const data = await resp.json();
  log('New round: ' + JSON.stringify(data, null, 2));
  showState(); // update UI
}

async function showState() {
  const resp = await fetch('/show_state');
  const data = await resp.json();
  if (data.error) {
    log(data.error);
    return;
  }
  // update hand display
  const handDiv = document.getElementById('playerHand');
  handDiv.innerHTML = '<h3>Your Hand</h3>';
  if (data.player_hand) {
    data.player_hand.forEach(card => {
      handDiv.innerHTML += '<span class="card">' + card + '</span>';
    });
  }

  // update scores
  const scoresDiv = document.getElementById('scores');
  scoresDiv.innerHTML = '<h3>Scores</h3>' +
    'You: ' + data.player_score + '<br>' +
    'Computer: ' + data.computer_score + '<br>' +
    'Bid winner: ' + data.bid_winner + ' @ ' + data.bid + '<br>' +
    'Trump suit: ' + (data.trump_suit || '(none)') + '<br>';
}

async function placeBid() {
  const bidVal = document.getElementById('bidValue').value;
  const resp = await fetch('/bid', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ player_bid: parseInt(bidVal) })
  });
  const data = await resp.json();
  log(JSON.stringify(data, null, 2));
  showState();
}

async function selectTrump() {
  const suit = document.getElementById('trumpSuit').value;
  const resp = await fetch('/select_trump', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ suit })
  });
  const data = await resp.json();
  log(JSON.stringify(data, null, 2));
  showState();
}

async function attachKitty() {
  const resp = await fetch('/attach_kitty', { method: 'POST' });
  const data = await resp.json();
  log(JSON.stringify(data, null, 2));
  showState();
}

async function playTrick() {
  let cardInput = document.getElementById('leadCard').value.trim();
  if (!cardInput) cardInput = null;
  const bodyObj = cardInput ? { lead_card: cardInput } : {};
  const resp = await fetch('/play_trick', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(bodyObj)
  });
  const data = await resp.json();
  if (data.error) {
    log('Error: ' + data.error);
  } else {
    if (data.trick_result) {
      log(data.trick_result);
    } else {
      log(JSON.stringify(data, null, 2));
    }
  }
  showState();
}

async function finalizeRound() {
  const resp = await fetch('/finalize_round', { method: 'POST' });
  const data = await resp.json();
  log('Finalize Round:\n' + JSON.stringify(data, null, 2));
  showState();
}

function log(msg) {
  document.getElementById('log').textContent += msg + "\\n";
}
</script>

</body>
</html>
"""
    return html_content

###############################################################################
#                                API ROUTES                                   #
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

    return jsonify({
        "message": "New round dealt.",
        "player_hand": current_game.get_player_hand_strings(0),
        "dealer_index": dealer_index
    })

@app.route("/bid", methods=["POST"])
def bid():
    global current_game, dealer_index
    if current_game is None:
        return jsonify({"error": "No game in progress. Call /new_round first."}), 400
    data = request.get_json() or {}
    player_bid = data.get("player_bid", 0)
    current_game.perform_bidding(dealer_index, player_bid)
    winner_name = current_game.players[current_game.bid_winner].name
    bid_amount = current_game.bid
    return jsonify({
        "message": f"Bidding complete. {winner_name} won the bid at {bid_amount}."
    })

@app.route("/select_trump", methods=["POST"])
def select_trump():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game in progress. /new_round first."}), 400
    if current_game.bid_winner is None:
        return jsonify({"error": "No bid winner yet. /bid first."}), 400
    bidder = current_game.players[current_game.bid_winner]

    data = request.get_json() or {}
    chosen_suit = data.get("suit")
    if bidder.name == "You":
        if chosen_suit not in ["Hearts", "Diamonds", "Clubs", "Spades"]:
            return jsonify({"error": "Invalid suit."}), 400
        current_game.set_trump_suit(chosen_suit)
        return jsonify({"message": f"You chose trump: {chosen_suit}."})
    else:
        # computer picks automatically
        comp_suit = current_game.computer_select_lead_card(bidder.hand)
        # That's not ideal, let's do a simpler approach:
        suits_in_hand = set(c.suit for c in bidder.hand)
        if suits_in_hand:
            picked = random.choice(list(suits_in_hand))
        else:
            picked = "Hearts"
        current_game.set_trump_suit(picked)
        return jsonify({"message": f"Computer chose trump: {picked}."})

@app.route("/attach_kitty", methods=["POST"])
def attach_kitty():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400
    if current_game.bid_winner is None:
        return jsonify({"error": "No bid winner. /bid first."}), 400
    if current_game.trump_suit is None:
        return jsonify({"error": "No trump set yet. /select_trump first."}), 400

    current_game.attach_kitty()
    current_game.allow_other_player_discard()

    return jsonify({
        "message": "Kitty attached and discard phase done.",
        "player_hand": current_game.get_player_hand_strings(0)
    })

@app.route("/play_trick", methods=["POST"])
def play_trick():
    global current_game, round_trick_count
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400
    data = request.get_json() or {}
    lead_card_str = data.get("lead_card")
    result_str = current_game.play_trick(lead_card_str)
    if "error" in result_str.lower():
        return jsonify({"error": result_str})
    round_trick_count += 1
    return jsonify({"trick_result": result_str})

@app.route("/finalize_round", methods=["POST"])
def finalize_round():
    global current_game, round_trick_count
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400
    if round_trick_count < 5:
        return jsonify({"error": "You haven't played all 5 tricks yet."}), 400

    final_info = current_game.finalize_hand()
    return jsonify({
        "round_result": final_info,
        "player_score": current_game.players[0].score,
        "computer_score": current_game.players[1].score
    })

@app.route("/show_state", methods=["GET"])
def show_state():
    global current_game
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400

    return jsonify({
        "player_hand": current_game.get_player_hand_strings(0),
        "player_score": current_game.players[0].score,
        "computer_hand_count": len(current_game.players[1].hand),
        "computer_score": current_game.players[1].score,
        "bid_winner": current_game.bid_winner,
        "bid": current_game.bid,
        "trump_suit": current_game.trump_suit
    })

###############################################################################
#                                 APP RUN                                     #
###############################################################################

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
