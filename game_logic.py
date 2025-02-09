import random
import time  # For delays in computer moves

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
        return {
            "suit": self.suit,
            "rank": self.rank,
            "text": f"{self.rank}{self.suit}",
            "selected": getattr(self, "selected", False)
        }

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
    "♣": ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9"],
    "♠": ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9"]
}

def is_trump(card, trump_suit):
    if card.suit == trump_suit:
        return True
    if card.suit == "♥" and card.rank == "A":  # Ace of Hearts is always trump.
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
        # Fixed rotation of computer names.
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
            names = random.sample(computer_names, 2)
            self.players = {
                "player": {"hand": [], "tricks": [], "score": 0},
                names[0]: {"hand": [], "tricks": [], "score": 0},
                names[1]: {"hand": [], "tricks": [], "score": 0}
            }
            self.player_order = ["player", names[0], names[1]]
        self.bidHistory = {}
        self.dealer = "player" if random.random() < 0.5 else self.player_order[1]
        self.kitty = []
        self.trump_suit = None
        self.phase = "bidding"  # bidding, trump, kitty, draw, trick, finished
        self.biddingMessage = ""
        self.currentTrick = []
        self.lastTrick = []  # Holds finished trick so it remains visible for a delay
        self.trickLog = []  # Overall hand log
        self.gameNotes = []  # All events persist during the game
        self.handScores = []  # Record of each hand's scoring summary
        self.currentTurn = None
        self.bidder = None
        self.bid = 0
        self.trumpCardsPlayed = []  # (player, card) tuples for trump cards played this hand
        self.deal_hands()

    def deal_hands(self):
        self.deck = Deck()
        self.trump_suit = None
        for p in self.players:
            self.players[p]["hand"] = self.deck.deal(5)
            self.players[p]["tricks"] = []
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.biddingMessage = "Place your bid (15, 20, 25, or 30)."
        self.currentTrick = []
        self.lastTrick = []
        self.trickLog = []
        self.bidHistory = {}
        # Do not clear gameNotes so they persist.
        self.trumpCardsPlayed = []
        if self.mode == "2p" and self.dealer == "player":
            comp_id = self.player_order[1]
            comp_bid, comp_trump = self.computer_bid(comp_id)
            self.bidHistory[comp_id] = "Passed" if comp_bid == 0 else f"bid {comp_bid}"
        self.currentTurn = "player"

    def computer_bid(self, comp_id):
        hand = self.players[comp_id]["hand"]
        has5 = any(card.rank == "5" for card in hand)
        topCount = sum(1 for card in hand if card.rank in ["J", "A", "K"])
        bid = 20 if has5 or topCount >= 2 else (15 if topCount == 1 else 0)
        suit_counts = {}
        for card in hand:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        best_suit = max(suit_counts, key=suit_counts.get)
        timestamp = time.strftime("%H:%M:%S")
        self.gameNotes.append(f"{timestamp} - {comp_id} " + ("Passed" if bid == 0 else f"bid {bid}"))
        return bid, best_suit

    def process_bid(self, player_bid):
        self.bidHistory["player"] = "Passed" if player_bid == 0 else f"bid {player_bid}"
        if self.mode == "2p":
            comp_id = self.player_order[1]
            if comp_id in self.bidHistory:
                comp_bid_str = self.bidHistory[comp_id]
                comp_bid = int(comp_bid_str.split()[1]) if "bid" in comp_bid_str else 0
            else:
                comp_bid, comp_trump = self.computer_bid(comp_id)
                self.bidHistory[comp_id] = "Passed" if comp_bid == 0 else f"bid {comp_bid}"
            if self.dealer == "player":
                if comp_bid == 0:
                    self.bidder = "player"
                    self.bid = 15
                    self.biddingMessage = "All passed. As dealer, you are bagged and automatically bid 15. Please select the trump suit."
                    timestamp = time.strftime("%H:%M:%S")
                    self.gameNotes.append(f"{timestamp} - Dealer automatically bid 15.")
                    self.phase = "trump"
                else:
                    if player_bid != 0 and player_bid != comp_bid + 5:
                        self.biddingMessage = f"As dealer, you must either pass or bid {comp_bid + 5}."
                        return
                    if player_bid == 0:
                        self.bidder = comp_id
                        self.bid = comp_bid
                        _, comp_trump = self.computer_bid(comp_id)
                        self.trump_suit = comp_trump
                        self.biddingMessage = f"{comp_id} wins the bid with {comp_bid} and has selected {comp_trump} as trump."
                        timestamp = time.strftime("%H:%M:%S")
                        self.gameNotes.append(f"{timestamp} - {comp_id} selected {comp_trump} as trump.")
                        self.phase = "draw"
                    else:
                        self.bidder = "player"
                        self.bid = player_bid
                        self.biddingMessage = f"Player bids {player_bid} and wins the bid. Please select the trump suit."
                        self.phase = "trump"
            else:
                if player_bid >= comp_bid:
                    self.bidder = "player"
                    self.bid = player_bid
                    self.bidHistory[comp_id] = "Passed"
                    self.biddingMessage = f"Player bids {player_bid} and wins the bid. Please select the trump suit."
                    self.phase = "trump"
                else:
                    self.bidder = comp_id
                    self.bid = comp_bid
                    _, comp_trump = self.computer_bid(comp_id)
                    self.trump_suit = comp_trump
                    self.biddingMessage = f"{comp_id} wins the bid with {comp_bid} and has selected {comp_trump} as trump."
                    timestamp = time.strftime("%H:%M:%S")
                    self.gameNotes.append(f"{timestamp} - {comp_id} selected {comp_trump} as trump.")
                    self.phase = "draw"
            self.currentTurn = self.bidder
        elif self.mode == "3p":
            comp1 = self.player_order[1]
            comp2 = self.player_order[2]
            comp_bid1, comp_trump1 = self.computer_bid(comp1)
            comp_bid2, comp_trump2 = self.computer_bid(comp2)
            self.bidHistory[comp1] = "Passed" if comp_bid1 == 0 else f"bid {comp_bid1}"
            self.bidHistory[comp2] = "Passed" if comp_bid2 == 0 else f"bid {comp_bid2}"
            bids = {"player": player_bid, comp1: comp_bid1, comp2: comp_bid2}
            highest_bidder = max(bids, key=bids.get)
            highest_bid = bids[highest_bidder]
            self.bidder = highest_bidder
            self.bid = highest_bid
            if highest_bidder == "player":
                self.biddingMessage = f"Player bids {player_bid} and wins the bid. Please select the trump suit."
                self.phase = "trump"
            else:
                if highest_bidder == comp1:
                    self.trump_suit = comp_trump1
                else:
                    self.trump_suit = comp_trump2
                self.biddingMessage = f"{highest_bidder} wins the bid with {highest_bid} and has selected {self.trump_suit} as trump."
                timestamp = time.strftime("%H:%M:%S")
                self.gameNotes.append(f"{timestamp} - {highest_bidder} selected {self.trump_suit} as trump.")
                self.phase = "draw"
            self.currentTurn = self.bidder
        return

    def select_trump(self, suit):
        if self.phase == "trump":
            self.trump_suit = suit
            self.biddingMessage = f"Player bids {self.bidHistory['player'].split()[1]} and wins the bid. Trump is set to {suit}."
            if self.bidder == "player":
                self.phase = "kitty"
            else:
                self.phase = "draw"
        return

    def confirm_kitty(self, keptIndices):
        if self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            new_hand = []
            for i in keptIndices:
                if i < len(combined):
                    card = combined[i]
                    card.selected = True
                    new_hand.append(card)
            if len(new_hand) < 1:
                new_hand = self.players["player"]["hand"][:1]
            if len(new_hand) > 5:
                new_hand = new_hand[:5]
            self.players["player"]["hand"] = new_hand
            self.biddingMessage = "Kitty selection confirmed. Proceeding to draw phase."
            self.phase = "draw"
        else:
            self.phase = "draw"
        return

    def confirm_draw(self, keptIndices=None):
        if keptIndices is not None:
            kept_cards = []
            for i in keptIndices:
                if i < len(self.players["player"]["hand"]):
                    card = self.players["player"]["hand"][i]
                    card.selected = getattr(card, "selected", True)
                    kept_cards.append(card)
            self.players["player"]["hand"] = kept_cards
        while len(self.players["player"]["hand"]) < 5 and len(self.deck.cards) > 0:
            self.players["player"]["hand"].append(self.deck.deal(1)[0])
        for card in self.players["player"]["hand"]:
            card.selected = False
        # Log computer draw info: if player is bidder then computer does not draw;
        # if computer is bidder, log the number of cards drawn.
        if self.bidder != "player":
            comp = self.bidder
            draw_count = 5 - len(self.players[comp]["hand"])
            for i in range(draw_count):
                if len(self.deck.cards) > 0:
                    self.players[comp]["hand"].append(self.deck.deal(1)[0])
            timestamp = time.strftime("%H:%M:%S")
            self.gameNotes.append(f"{timestamp} - {comp} drew {draw_count} card(s) in draw phase.")
        else:
            # For player bidder, log that computer did not draw.
            comp = self.player_order[1]
            timestamp = time.strftime("%H:%M:%S")
            self.gameNotes.append(f"{timestamp} - {comp} did not draw any cards in draw phase.")
        self.biddingMessage = "Draw complete. Proceeding to trick play."
        self.phase = "trick"
        self.currentTurn = self.bidder
        self.auto_play()
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
        card.selected = True
        self.currentTrick.append({"player": player, "card": card})
        timestamp = time.strftime("%H:%M:%S")
        if player != "player":
            self.gameNotes.append(f"{timestamp} - {player} played {card}")
        else:
            self.gameNotes.append(f"{timestamp} - Player played {card}")
        self.currentTurn = self.next_player(player)
        self.auto_play()
        if len(self.currentTrick) == len(self.player_order):
            self.finish_trick()
        return

    def auto_play(self):
        # Reduced delay: 0.5 sec → 0.33 sec.
        while self.currentTurn != "player" and len(self.currentTrick) < len(self.player_order):
            time.sleep(0.33)
            available = self.players[self.currentTurn]["hand"]
            if not available:
                break
            idx = random.randrange(len(available))
            self.play_card(self.currentTurn, idx)
        return

    def finish_trick(self):
        winner = self.evaluate_trick(self.currentTrick)
        timestamp = time.strftime("%H:%M:%S")
        trick_summary = f"{timestamp} - " + ", ".join(f"{entry['player']} played {entry['card']}" for entry in self.currentTrick)
        trick_summary += f". Winner: {winner}."
        self.gameNotes.append(trick_summary)
        self.trickLog.append(trick_summary)
        self.players[winner]["tricks"].append(self.currentTrick.copy())
        for entry in self.currentTrick:
            if is_trump(entry["card"], self.trump_suit):
                self.trumpCardsPlayed.append((entry["player"], entry["card"]))
        # Copy the finished trick into lastTrick so both cards are visible.
        self.lastTrick = self.currentTrick.copy()
        # Reduced delay: 2 sec → ~1.3 sec.
        time.sleep(1.3)
        # Clear currentTrick so next trick starts with an empty area.
        self.currentTrick = []
        # (We leave lastTrick intact so the UI can display the final trick until the next update.)
        self.currentTurn = winner
        if all(len(self.players[p]["hand"]) == 0 for p in self.players):
            self.complete_hand()
        else:
            if self.currentTurn != "player":
                time.sleep(0.33)
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
        bonus_winner = None
        bonus_value = 5
        if self.trumpCardsPlayed:
            bonus_winner, bonus_card = max(self.trumpCardsPlayed, key=lambda x: get_trump_value(x[1], self.trump_suit))
        elif self.currentTurn:
            bonus_winner = self.currentTurn
        if bonus_winner:
            points[bonus_winner] += bonus_value
        if self.bidder in points and points[self.bidder] < self.bid:
            points[self.bidder] = -self.bid
        hand_summary_parts = []
        for p in self.players:
            hand_points = points[p]
            total = self.players[p]["score"] + hand_points
            name = "Player" if p == "player" else p
            hand_summary_parts.append(f"{name}: {hand_points}/{total}")
            self.players[p]["score"] = total
        summary = "Hand over. " + " | ".join(hand_summary_parts)
        self.trickLog.append(summary)
        self.handScores.append(summary)
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
            "scoreboard": " | ".join(f"{'Player' if p=='player' else p}: {self.players[p]['score']}" for p in self.players),
            "currentTurn": self.currentTurn,
            "dealer": self.dealer,
            "gameNotes": self.gameNotes,
            "handScores": self.handScores,
            "mode": self.mode
        }
        if self.phase == "kitty" and self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            state["combinedHand"] = [card.to_dict() for card in combined]
        if self.phase == "draw":
            state["drawHand"] = [card.to_dict() for card in self.players["player"]["hand"]]
        if self.mode == "2p":
            comp = self.player_order[1]
            state["computerDiscardCount"] = 5 - len(self.players[comp]["hand"])
        if self.phase == "finished":
            state["scoreSheet"] = "\n".join(self.handScores)
        return state
