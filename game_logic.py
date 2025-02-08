import random

# ---------------------------
# Card and Deck Classes
# ---------------------------
class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g., "♥", "♦", "♣", "♠"
        self.rank = rank  # e.g., "2", "3", …, "10", "J", "Q", "K", "A"

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self):
        # Map face card letters to full lowercase names.
        rank_map = {"A": "ace", "J": "jack", "Q": "queen", "K": "king"}
        # Map suit symbols to full lowercase names.
        suit_map = {"♥": "hearts", "♦": "diamonds", "♣": "clubs", "♠": "spades"}
        # If rank is a face card, convert it; otherwise, use the number as-is.
        rank_str = rank_map.get(self.rank, self.rank)
        suit_str = suit_map.get(self.suit, self.suit)
        # Construct the image filename in the format: "rank_of_suit.png"
        # For example: "ace_of_hearts.png", "10_of_clubs.png", etc.
        img_url = f"cards/{rank_str}_of_{suit_str}.png"
        return {"suit": self.suit, "rank": self.rank, "img": img_url}

class Deck:
    def __init__(self):
        suits = ["♥", "♦", "♣", "♠"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards to deal.")
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

# ---------------------------
# Ranking Definitions (Simplified)
# ---------------------------
TRUMP_RANKINGS = {
    "♦": ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "♥": ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "♣": ["5", "J", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"],
    "♠": ["5", "J", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"]
}
OFFSUIT_RANKINGS = {
    "♦": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "♥": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "♣": ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "♠": ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
}

def is_trump(card, trump_suit):
    if card.suit == trump_suit:
        return True
    if card.suit == "♥" and card.rank == "A":
        return True
    return False

def get_trump_value(card, trump_suit):
    ranking = TRUMP_RANKINGS[trump_suit]
    return len(ranking) - ranking.index(card.rank)

def get_offsuit_value(card):
    ranking = OFFSUIT_RANKINGS[card.suit]
    return len(ranking) - ranking.index(card.rank)

# ---------------------------
# Game Class
# ---------------------------
class Game:
    def __init__(self, mode="2p", instructional=False):
        self.mode = mode
        self.instructional = instructional
        self.deck = None

        # Define computer names from a rotation.
        computer_names = ["Jack", "Jennifer", "Patrick", "John", "Liam", "Mary",
                          "Jasper", "Felix", "Holly", "Tom", "Karen", "Stephen",
                          "Leona", "Bill", "Christine", "Chris", "Henry"]

        if self.mode == "2p":
            self.computer_name = random.choice(computer_names)
            self.players = {
                "player": {"hand": [], "tricks": [], "score": 0},
                self.computer_name: {"hand": [], "tricks": [], "score": 0}
            }
            self.player_order = ["player", self.computer_name]
        elif self.mode == "3p":
            names = random.sample(computer_names, 2)
            self.players = {
                "player": {"hand": [], "tricks": [], "score": 0},
                names[0]: {"hand": [], "tricks": [], "score": 0},
                names[1]: {"hand": [], "tricks": [], "score": 0}
            }
            self.player_order = ["player", names[0], names[1]]

        self.bidHistory = {}  # e.g., {"player": "bid 15", "Bill": "Passed"}
        # Dealer: for 2p, choose randomly; for 3p, start with "player".
        if self.mode == "2p":
            self.dealer = "player" if random.random() < 0.5 else self.player_order[1]
        else:
            self.dealer = "player"
        self.kitty = []
        self.trump_suit = None
        self.phase = "bidding"  # bidding, trump, kitty, draw, trick, finished
        self.biddingMessage = ""
        self.currentTrick = []   # Cards played in the current trick
        self.lastTrick = []      # The last trick played (to display on the table)
        self.trickLog = []       # Summaries for each trick and hand
        self.currentTurn = None  # Who’s turn to play
        self.bidder = None       # Who won the bid
        self.bid = 0             # Winning bid value
        self.deal_hands()

    def deal_hands(self):
        self.deck = Deck()
        self.trump_suit = None  # Clear trump suit from previous hand
        for p in self.players:
            self.players[p]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.biddingMessage = "Place your bid (15, 20, 25, or 30)."
        self.currentTrick = []
        self.lastTrick = []
        self.trickLog = []
        self.bidHistory = {}
        self.currentTurn = None

    def computer_bid(self, comp_id):
        hand = self.players[comp_id]["hand"]
        has5 = any(card.rank == "5" for card in hand)
        topCount = sum(1 for card in hand if card.rank in ["J", "A", "K"])
        bid = 20 if has5 or topCount >= 2 else (15 if topCount == 1 else 0)
        suit_counts = {}
        for card in hand:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        best_suit = max(suit_counts, key=suit_counts.get)
        return bid, best_suit

    def process_bid(self, player_bid):
        self.bidHistory["player"] = "Passed" if player_bid == 0 else f"bid {player_bid}"
        if self.mode == "2p":
            comp_id = self.player_order[1]
            comp_bid, comp_trump = self.computer_bid(comp_id)
            self.bidHistory[comp_id] = "Passed" if comp_bid == 0 else f"bid {comp_bid}"
            if player_bid >= comp_bid:
                self.bidder = "player"
                self.bid = player_bid
                self.biddingMessage = f"You {self.bidHistory['player']} vs {comp_id} {self.bidHistory[comp_id]}. You win the bid. Select trump."
                self.phase = "trump"
            else:
                self.bidder = comp_id
                self.bid = comp_bid
                self.trump_suit = comp_trump
                self.biddingMessage = f"You {self.bidHistory['player']} vs {comp_id} {self.bidHistory[comp_id]}. {comp_id} wins the bid. (Dealer sees both bids.)"
                self.phase = "kitty"
            self.currentTurn = self.bidder
        elif self.mode == "3p":
            comp1 = self.player_order[1]
            comp2 = self.player_order[2]
            comp_bid1, comp_trump1 = self.computer_bid(comp1)
            comp_bid2, comp_trump2 = self.computer_bid(comp2)
            self.bidHistory[comp1] = "Passed" if comp_bid1 == 0 else f"bid {comp_bid1}"
            self.bidHistory[comp2] = "Passed" if comp_bid2 == 0 else f"bid {comp_bid2}"
            bids = {"player": player_bid, comp1: comp_bid1, comp2: comp_bid2}
            best_bidder = max(bids, key=bids.get)
            best_bid = bids[best_bidder]
            self.bidder = best_bidder
            self.bid = best_bid
            if best_bidder == "player":
                self.biddingMessage = f"Bids: player {self.bidHistory['player']}, {comp1} {self.bidHistory[comp1]}, {comp2} {self.bidHistory[comp2]}. You win the bid. Select trump."
                self.phase = "trump"
            else:
                self.biddingMessage = f"Bids: player {self.bidHistory['player']}, {comp1} {self.bidHistory[comp1]}, {comp2} {self.bidHistory[comp2]}. {best_bidder} wins the bid and chooses trump."
                if best_bidder == comp1:
                    self.trump_suit = comp_trump1
                else:
                    self.trump_suit = comp_trump2
                self.phase = "kitty"
            self.currentTurn = self.bidder
            if all(bid == 0 for bid in bids.values()):
                if self.dealer == "player":
                    self.bidder = "player"
                    self.bid = 15
                    self.bidHistory["player"] = "bid 15"
                    self.biddingMessage = "All passed. As dealer, you are bagged. You must bid 15 and select trump."
                    self.phase = "trump"
                    self.currentTurn = "player"
                else:
                    self.bidder = self.dealer
                    self.bid = 15
                    self.bidHistory[self.dealer] = "bid 15"
                    self.biddingMessage = f"All passed. {self.dealer} is bagged and bids 15."
                    self.phase = "kitty"
                    self.currentTurn = self.dealer
        return

    def select_trump(self, suit):
        if self.phase == "trump":
            self.trump_suit = suit
            self.phase = "kitty"
        return

    def confirm_kitty(self, keptIndices):
        if self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            new_hand = [combined[i] for i in keptIndices if i < len(combined)]
            if len(new_hand) < 1:
                new_hand = self.players["player"]["hand"][:1]
            if len(new_hand) > 5:
                new_hand = new_hand[:5]
            self.players["player"]["hand"] = new_hand
        self.phase = "draw"
        return

    def confirm_draw(self):
        if self.bidder == "player":
            while len(self.players["player"]["hand"]) < 5 and len(self.deck.cards) > 0:
                self.players["player"]["hand"].append(self.deck.deal(1)[0])
        self.phase = "trick"
        self.currentTurn = self.bidder
        self.auto_play()
        return

    def next_player(self, current):
        idx = self.player_order.index(current)
        next_idx = (idx + 1) % len(self.player_order)
        return self.player_order[next_idx]

    def play_card(self, player, cardIndex):
        if self.currentTurn != player:
            return
        if cardIndex < 0 or cardIndex >= len(self.players[player]["hand"]):
            return
        card = self.players[player]["hand"].pop(cardIndex)
        self.currentTrick.append({"player": player, "card": card})
        self.currentTurn = self.next_player(player)
        self.auto_play()
        if len(self.currentTrick) == len(self.player_order):
            self.finish_trick()
        return

    def auto_play(self):
        while self.currentTurn != "player" and len(self.currentTrick) < len(self.player_order):
            available = self.players[self.currentTurn]["hand"]
            if not available:
                break
            idx = random.randrange(len(available))
            self.play_card(self.currentTurn, idx)
        return

    def finish_trick(self):
        winner = self.evaluate_trick(self.currentTrick)
        trick_summary = ", ".join(f"{entry['player']} played {entry['card']}" for entry in self.currentTrick)
        trick_summary += f". Winner: {winner}."
        self.trickLog.append(trick_summary)
        self.players[winner]["tricks"].append(self.currentTrick.copy())
        self.lastTrick = self.currentTrick.copy()  # Save for display.
        self.currentTrick = []
        self.currentTurn = winner  # Winner leads next trick.
        if all(len(self.players[p]["hand"]) == 0 for p in self.players):
            self.complete_hand()
        return

    def evaluate_trick(self, trick):
        if not trick:
            return None
        lead_suit = trick[0]["card"].suit
        trump_plays = [entry for entry in trick if is_trump(entry["card"], self.trump_suit)]
        if trump_plays:
            winner_entry = max(trump_plays, key=lambda x: get_trump_value(x["card"], self.trump_suit))
        else:
            follow_plays = [entry for entry in trick if entry["card"].suit == lead_suit]
            if follow_plays:
                winner_entry = max(follow_plays, key=lambda x: get_offsuit_value(x["card"]))
            else:
                winner_entry = trick[0]
        return winner_entry["player"]

    def complete_hand(self):
        points = {p: len(self.players[p]["tricks"]) * 5 for p in self.players}
        if self.trickLog:
            last = self.trickLog[-1]
            for p in self.players:
                if f"Winner: {p}" in last:
                    points[p] += 5
                    break
        if self.bidder in points and points[self.bidder] < self.bid:
            points[self.bidder] = -self.bid
        for p in self.players:
            self.players[p]["score"] += points[p]
        summary = "Hand over. " + " | ".join(f"{p}: {self.players[p]['score']}" for p in self.players)
        self.trickLog.append(summary)
        if any(self.players[p]["score"] >= 120 for p in self.players):
            self.phase = "finished"
        else:
            self.new_hand()
        return

    def new_hand(self):
        current_idx = self.player_order.index(self.dealer)
        next_idx = (current_idx + 1) % len(self.player_order)
        self.dealer = self.player_order[next_idx]
        self.deal_hands()
        return

    def to_dict(self):
        wonTricks = {p: len(self.players[p]["tricks"]) for p in self.players}
        state = {
            "gamePhase": self.phase,
            "playerHand": [card.to_dict() for card in self.players["player"]["hand"]],
            "computerHandCount": (len(self.players[self.player_order[1]]["hand"]) if self.mode=="2p" else None),
            "computer1HandCount": (len(self.players[self.player_order[1]]["hand"]) if self.mode=="3p" else None),
            "computer2HandCount": (len(self.players[self.player_order[2]]["hand"]) if self.mode=="3p" else None),
            "kitty": [card.to_dict() for card in self.kitty] if self.phase in ["bidding", "kitty"] else [],
            "trumpSuit": self.trump_suit if self.phase not in ["bidding"] else None,
            "biddingMessage": self.biddingMessage,
            "bidHistory": self.bidHistory,
            "currentTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.currentTrick],
            "lastTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.lastTrick],
            "trickLog": self.trickLog,
            "wonTricks": wonTricks,
            "scoreboard": " | ".join(f"{p}: {self.players[p]['score']}" for p in self.players),
            "currentTurn": self.currentTurn,
            "dealer": self.dealer
        }
        if self.phase == "kitty" and self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            state["combinedHand"] = [card.to_dict() for card in combined]
        if self.phase == "draw":
            state["drawHand"] = [card.to_dict() for card in self.players["player"]["hand"]]
        if self.phase == "finished":
            state["scoreSheet"] = "\n".join(self.trickLog)
        return state
