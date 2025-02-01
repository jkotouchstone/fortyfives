from flask import Flask, request, jsonify, render_template_string, send_from_directory
import random, math

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# Global variables for game mode and the current game.
game_mode = None  # "headsup", "cutthroat", "partners", or "5way"
current_game = None

#################################
#         GAME CLASSES          #
#################################

# --- Utility: A standard deck of cards (or multiple decks if needed) ---
class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g., "Hearts"
        self.rank = rank  # e.g., "A", "7", etc.
    def __str__(self):
        return f"{self.rank} of {self.suit}"

# We'll use one deck for up to 5 players.
class Deck:
    def __init__(self, num_decks=1):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = []
        for _ in range(num_decks):
            self.cards.extend([Card(s, r) for s in suits for r in ranks])
            # Ensure the 5 of Hearts is in the deck
            if not any(str(c) == "5 of Hearts" for c in self.cards):
                self.cards.append(Card("Hearts", "5"))
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self, num_cards):
        dealt = [self.cards.pop(0) for _ in range(num_cards)]
        return dealt

# --- Scoring and ranking constants ---
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
    """
    Returns a numeric rank for a card.
    If trump is one of "Diamonds", "Clubs", or "Spades", a trump dictionary is used.
    Otherwise, RANK_PRIORITY is used.
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

# --- Player class ---
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []  # Cards collected from tricks
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    def trump_count(self, trump):
        return sum(1 for card in self.hand if card.suit == trump)
    def discard_auto(self, trump):
        # Automatically keep all trump cards.
        trump_cards = [card for card in self.hand if card.suit == trump]
        non_trump = [card for card in self.hand if card.suit != trump]
        # In our simplified rule, player discards all non-trump cards.
        self.hand = trump_cards  # In case trump_cards > 5, later we trim to 5.
        # Then, if hand still > 5, keep highest-ranking trump cards.
        if len(self.hand) > 5:
            self.hand.sort(key=lambda card: get_card_rank(str(card), trump), reverse=True)
            self.hand = self.hand[:5]
        return  # Discards are determined automatically.
    
# --- Game class ---
class Game:
    def __init__(self, mode):
        self.mode = mode  # "headsup", "cutthroat", "partners", "5way"
        self.players = self.initialize_players(mode)
        self.num_players = len(self.players)
        # For all modes we deal 5 cards per player and 3 kitty cards.
        self.deck = Deck(num_decks=1)
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # index of the player who won the bid
        self.bid = 0            # Winning bid value
        self.leading_player = None  # index of the player who leads the trick
        self.trick_count = 0
        self.played_cards_log = []  # list of tuples: (card, player_index) for current trick
        self.hand_log = []  # for recording this hand’s trick-by-trick results (optional)
        self.starting_scores = {p.name: p.score for p in self.players}
    def initialize_players(self, mode):
        if mode == "headsup":
            return [Player("You"), Player("Computer")]
        elif mode == "cutthroat":
            return [Player("You"), Player("Computer A"), Player("Computer B")]
        elif mode == "partners":
            # Team 1: You, Partner; Team 2: Opponent A, Opponent B
            return [Player("You"), Player("Partner"), Player("Opponent A"), Player("Opponent B")]
        elif mode == "5way":
            return [Player("You"), Player("Computer A"), Player("Computer B"), Player("Computer C"), Player("Computer D")]
        else:
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
        # For the winning bidder, automatically discard all non-trump cards.
        # (In a real game the player might choose, but here we simulate automatic discarding.)
        bidder = self.players[bidder_index]
        bidder.discard_auto(self.trump_suit)
        return {"player_hand": [str(c) for c in bidder.hand]}
    def play_trick(self, played_card=None):
        """
        For a multiplayer trick:
         - The trick proceeds in order starting from the current lead index.
         - Each player (including computer players) plays one card.
         - For computer players, a card is chosen automatically from valid options.
         - The winner is determined by:
            * If one or more trump cards are played, the highest trump wins.
            * Otherwise, the highest card in the lead suit wins.
         - Award 5 points to the winner.
         - Append the played cards to that player's trick pile.
         - Advance the lead to the winner.
         - Increase trick count.
         - When 5 tricks have been played (or players run out of cards), end the hand.
        """
        num = self.num_players
        # Determine the turn order based on self.leading_player (an index)
        order = [(self.leading_player + i) % num for i in range(num)]
        played = {}  # mapping player index -> card played (as string)
        # For the human player (assumed to be index 0), if played_card is provided, use it.
        # For computer players, auto-select a card.
        for idx in order:
            p = self.players[idx]
            if idx == 0:
                # Human player:
                if played_card is None:
                    return {"trick_result": "Awaiting your play.", "current_trick_cards": []}, None
                # Validate that the human's card is in their hand.
                if played_card not in [str(c) for c in p.hand]:
                    return {"trick_result": "Invalid card.", "current_trick_cards": []}, None
                card_obj = next(c for c in p.hand if str(c)==played_card)
                p.hand.remove(card_obj)
                played[idx] = card_obj
            else:
                # Computer: auto-select a valid card.
                valid = [card for card in p.hand if card.suit == self.players[order[0]].hand[0].suit] if p.hand else []
                # For simplicity, if they have any card, pick a random one.
                if p.hand:
                    card_obj = random.choice(p.hand)
                    p.hand.remove(card_obj)
                    played[idx] = card_obj
                else:
                    played[idx] = None
        # Determine lead suit from the first card played.
        lead_suit = played[order[0]].suit if played[order[0]] else None
        # Determine winning card:
        winning_idx = None
        winning_rank = -1
        for idx, card in played.items():
            if not card: continue
            # If card is trump, treat its rank from trump dictionary; otherwise if it follows lead suit use normal rank.
            if card.suit == self.trump_suit:
                rank_val = get_card_rank(str(card), trump=self.trump_suit)
            elif card.suit == lead_suit:
                rank_val = get_card_rank(str(card))
            else:
                rank_val = -1  # not eligible unless no card followed suit
            if rank_val > winning_rank:
                winning_rank = rank_val
                winning_idx = idx
        # Award trick:
        trick_cards = [str(card) for card in played.values() if card is not None]
        if winning_idx is not None:
            self.players[winning_idx].score += 5
            self.players[winning_idx].tricks_won += 1
            self.players[winning_idx].trick_pile.extend(trick_cards)
            self.leading_player = winning_idx
            result_text = f"Trick won by {self.players[winning_idx].name}."
        else:
            result_text = "No winner determined for the trick."
        self.trick_count += 1
        # End-of-hand processing: if 5 tricks have been played (or hands empty), end hand.
        if self.trick_count >= 5 or any(len(p.hand)==0 for p in self.players):
            # Determine bonus for highest card played this hand.
            best_card = None
            best_player = None
            best_val = -1
            # Look over all played cards in this hand (we could store them in a log)
            for p in self.players:
                for card in p.trick_pile:
                    val = get_card_rank(card, trump=self.trump_suit)
                    if val > best_val:
                        best_val = val
                        best_card = card
                        best_player = p.name
            bonus_text = ""
            if best_player is not None:
                for p in self.players:
                    if p.name == best_player:
                        p.score += BONUS_POINTS
                        bonus_text = f" Highest card was {best_card}. Bonus {BONUS_POINTS} points to {best_player}."
                        break
            result_text += bonus_text
            # (Bid adjustments could be applied here if desired.)
            # Hand over: return hand results.
            hand_scores = {p.name: p.score - self.starting_scores[p.name] for p in self.players}
            result_text += " Hand scores: " + ", ".join([f"{name} {score}" for name, score in hand_scores.items()])
            return {"trick_result": result_text, "current_trick_cards": trick_cards}, hand_scores
        else:
            return {"trick_result": result_text, "current_trick_cards": trick_cards}, None

#################################
#           ROUTES              #
#################################

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global game_mode, current_game
    data = request.json
    mode = data.get("mode", "headsup")
    game_mode = mode
    # Initialize a new Game with the chosen mode.
    current_game = Game(mode)
    return jsonify({"mode": mode})

@app.route("/deal_cards", methods=["POST"])
def deal_cards():
    global current_game, current_dealer
    if current_game is None:
        return jsonify({"error": "Game mode not set. Please select a game mode."}), 400
    current_game.deal_hands()
    current_game.starting_scores = {p.name: p.score for p in current_game.players}
    # For simplicity, assign dealer: alternate between modes (or choose randomly)
    current_dealer = current_game.players[0].name  # In multiplayer, you might decide dealer differently.
    return jsonify({"player_hand": [str(c) for c in current_game.players[0].hand], "dealer": current_dealer, "mode": game_mode})

@app.route("/computer_first_bid", methods=["POST"])
def computer_first_bid():
    # For simplicity, generate one random bid for the computers (even if there are more than one).
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def submit_bid():
    try:
        if current_game is None:
            return jsonify({"error": "No game in progress. Please set a game mode and deal cards first."}), 400
        data = request.json
        player_bid = data.get("player_bid", 0)
        comp_bid = data.get("computer_bid", 0)
        if player_bid == 0:
            comp_bid = random.choice([15, 20, 25, 30])
        if comp_bid > player_bid:
            trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
            kitty = current_game.confirm_trump(trump_suit)
            current_game.bid_winner = 1  # Computer wins bid
            current_game.bid = comp_bid
            current_game.leading_player = 1  # For now, assume computer (first computer) leads.
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer", "trump_suit": trump_suit, "kitty_cards": kitty})
        else:
            current_game.bid_winner = 0  # Human wins bid
            current_game.bid = player_bid
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
    # In the new (automatic) discard phase, the winning bidder's hand is trimmed automatically.
    result = current_game.discard_phase(current_game.bid_winner)
    return jsonify(result)

@app.route("/attach_kitty", methods=["POST"])
def attach_kitty():
    data = request.json
    keep_cards = data.get("keep_cards", [])
    # In a manual kitty phase, the winning bidder selects which kitty cards to add.
    bidder = current_game.players[current_game.bid_winner]
    for card_str in keep_cards:
        for c in current_game.kitty:
            if str(c) == card_str:
                bidder.hand.append(c)
    current_game.kitty = [c for c in current_game.kitty if str(c) not in keep_cards]
    return jsonify({"player_hand": [str(c) for c in current_game.players[0].hand]})
    
@app.route("/play_trick", methods=["POST"])
def play_trick():
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

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
