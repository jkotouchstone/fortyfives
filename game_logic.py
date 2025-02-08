import random
import time  # Used for delays in computer moves

# ---------------------------
# Card and Deck Classes
# ---------------------------
class Card:
    def __init__(self, suit, rank):
        self.suit = suit      # e.g., "♥", "♦", "♣", "♠"
        self.rank = rank      # e.g., "2", "3", …, "10", "J", "Q", "K", "A"

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self):
        # Return plain-text representation.
        return {"suit": self.suit, "rank": self.rank, "text": f"{self.rank}{self.suit}"}

class Deck:
    def __init__(self):
        suits = ["♥", "♦", "♣", "♠"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(s, r) for s in suits for r in ranks]
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards to deal.")
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

# ---------------------------
# Ranking Definitions
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
    # Ace of Hearts is always trump.
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

        # Use a list of computer names.
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
        else:
            # (For simplicity, 3p mode follows similar logic.)
            names = random.sample(computer_names, 2)
            self.players = {
                "player": {"hand": [], "tricks": [], "score": 0},
                names[0]: {"hand": [], "tricks": [], "score": 0},
                names[1]: {"hand": [], "tricks": [], "score": 0}
            }
            self.player_order = ["player", names[0], names[1]]

        self.bidHistory = {}  # e.g., {"player": "bid 15", "Bill": "Passed"}
        # For heads-up, choose dealer randomly.
        if self.mode == "2p":
            self.dealer = "player" if random.random() < 0.5 else self.player_order[1]
        else:
            self.dealer = "player"
        self.kitty = []
        self.trump_suit = None
        self.phase = "bidding"   # Possible phases: "bidding", "trump", "kitty", "draw", "trick", "finished"
        self.biddingMessage = ""
        self.currentTrick = []   # Cards played in the current trick
        self.lastTrick = []      # Stores the last trick so played cards remain visible briefly
        self.trickLog = []       # Summaries for each trick and hand
        self.currentTurn = None  # Whose turn it is to play
        self.bidder = None       # Who won the bid
        self.bid = 0             # Winning bid value
        self.deal_hands()

    def deal_hands(self):
        self.deck = Deck()
        self.trump_suit = None
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
            # Display both bids so the dealer sees what the computer did.
            if player_bid >= comp_bid:
                self.bidder = "player"
                self.bid = player_bid
                self.biddingMessage = f"Player bids {player_bid} and wins the bid. Waiting for trump selection."
                self.phase = "trump"
            else:
                self.bidder = comp_id
                self.bid = comp_bid
                self.trump_suit = comp_trump  # Computer auto-selects trump.
                self.biddingMessage = f"{comp_id} bids {comp_bid} and wins the bid; {comp_id} has selected {comp_trump} as trump."
                self.phase = "draw"
            self.currentTurn = self.bidder
        # (3p mode can be handled similarly.)
        return

    def select_trump(self, suit):
        if self.phase == "trump":
            self.trump_suit = suit
            # If player is bidder, move to kitty phase; otherwise, go directly to draw.
            if self.bidder == "player":
                self.phase = "kitty"
            else:
                self.phase = "draw"
        return

    def confirm_kitty(self, keptIndices):
        # This phase only applies if the player is the bidder.
        if self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            new_hand = [combined[i] for i in keptIndices if i < len(combined)]
            if len(new_hand) < 1:
                new_hand = self.players["player"]["hand"][:1]  # Ensure at least one card is kept.
            if len(new_hand) > 5:
                new_hand = new_hand[:5]
            self.players["player"]["hand"] = new_hand
            self.phase = "draw"
        else:
            self.phase = "draw"
        return

    def confirm_draw(self, keptIndices=None):
        # In the draw phase, allow the player to select which cards to keep.
        if keptIndices is not None:
            kept_cards = [self.players["player"]["hand"][i] for i in keptIndices if i < len(self.players["player"]["hand"])]
            self.players["player"]["hand"] = kept_cards
        # Draw replacement cards until there are 5 cards.
        while len(self.players["player"]["hand"]) < 5 and len(self.deck.cards) > 0:
            self.players["player"]["hand"].append(self.deck.deal(1)[0])
        self.phase = "trick"
        self.currentTurn = self.bidder  # Trick play starts with the bidder.
        self.auto_play()  # In case the computer is to lead.
        return

    def next_player(self, current):
        idx = self.player_order.index(current)
        return self.player_order[(idx + 1) % len(self.player_order)]

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
        # If it's not the player's turn, computer(s) play with a 0.5-second delay.
        while self.currentTurn != "player" and len(self.currentTrick) < len(self.player_order):
            time.sleep(0.5)
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
        self.lastTrick = self.currentTrick.copy()  # Keep played cards visible until the next trick.
        self.currentTrick = []
        self.currentTurn = winner  # Winner leads the next trick.
        if all(len(self.players[p]["hand"]) == 0 for p in self.players):
            self.complete_hand()
        else:
            if self.currentTurn != "player":
                time.sleep(0.5)
                self.auto_play()
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
        summary = "Hand over. " + " | ".join(f"{'Player' if p=='player' else p}: {self.players[p]['score']}" for p in self.players)
        self.trickLog.append(summary)
        if any(self.players[p]["score"] >= 120 for p in self.players):
            self.phase = "finished"
        else:
            self.new_hand()
        return

    def new_hand(self):
        current_idx = self.player_order.index(self.dealer)
        self.dealer = self.player_order[(current_idx + 1) % len(self.player_order)]
        self.deal_hands()
        return

    def to_dict(self):
        wonTricks = {p: len(self.players[p]["tricks"]) for p in self.players}
        state = {
            "gamePhase": self.phase,
            "playerHand": [card.to_dict() for card in self.players["player"]["hand"]],
            "computerHandCount": (len(self.players[self.player_order[1]]["hand"]) if self.mode == "2p" else None),
            "kitty": [card.to_dict() for card in self.kitty] if self.phase in ["bidding", "kitty"] else [],
            "trumpSuit": self.trump_suit if self.phase not in ["bidding"] else None,
            "biddingMessage": self.biddingMessage,
            "bidHistory": self.bidHistory,
            "currentTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.currentTrick],
            "lastTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.lastTrick],
            "trickLog": self.trickLog,
            "wonTricks": wonTricks,
            "scoreboard": " | ".join(f"{'Player' if p=='player' else p}: {self.players[p]['score']}" for p in self.players),
            "currentTurn": self.currentTurn,
            "dealer": self.dealer
        }
        # For kitty phase, send combined hand (player's hand + kitty)
        if self.phase == "kitty" and self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            state["combinedHand"] = [card.to_dict() for card in combined]
        # For draw phase, send draw hand (player's current hand)
        if self.phase == "draw":
            state["drawHand"] = [card.to_dict() for card in self.players["player"]["hand"]]
        if self.phase == "finished":
            state["scoreSheet"] = "\n".join(self.trickLog)
        return state
