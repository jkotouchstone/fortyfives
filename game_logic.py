import random
import time

# ---------------------------
# Card and Deck Classes
# ---------------------------
class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g., "♥", "♦", "♣", "♠"
        self.rank = rank  # e.g., "2", "3", …, "10", "J", "Q", "K", "A"
        self.text = f"{self.rank}{self.suit}"  # Unique identifier

    def __str__(self):
        return self.text

    def to_dict(self):
        return {
            "suit": self.suit,
            "rank": self.rank,
            "text": self.text,
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
        self.computerDrawCounts = {}
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
        self.phase = "bidding"
        self.biddingMessage = "Place your bid (15, 20, 25, or 30). Dealer: " + self.dealer
        self.currentTrick = []
        self.lastTrick = []  # For temporarily displaying played cards
        self.trickLog = []
        self.gameNotes = []
        self.handScores = []
        self.currentTurn = None
        self.bidder = None
        self.bid = 0
        self.trumpCardsPlayed = []
        self.combinedHand = []
        self.trick_count = 0  # Initialize trick counter for the hand
        self.deal_hands()

    def next_player(self, current):
        idx = self.player_order.index(current)
        return self.player_order[(idx + 1) % len(self.player_order)] if self.player_order else "player"

    def deal_hands(self):
        self.deck = Deck()
        self.trump_suit = None
        for p in self.players:
            self.players[p]["hand"] = self.deck.deal(5)
            self.players[p]["tricks"] = []
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.biddingMessage = "Place your bid (15, 20, 25, or 30). Dealer: " + self.dealer
        self.currentTrick = []
        self.lastTrick = []
        self.trickLog = []
        self.bidHistory = {}
        self.trumpCardsPlayed = []
        self.combinedHand = []
        self.computerDrawCounts = {}
        self.trick_count = 0  # Reset trick counter for each hand
        if self.mode == "2p" and self.dealer == "player":
            comp_id = self.player_order[1]
            comp_bid, comp_trump = self.computer_bid(comp_id)
            self.bidHistory[comp_id] = "Passed" if comp_bid == 0 else f"bid {comp_bid}"
        self.currentTurn = "player"

    def computer_bid(self, comp_id):
        hand = self.players[comp_id]["hand"]
        has5 = any(card.rank == "5" for card in hand)
        topCount = sum(1 for card in hand if card.rank in ["J", "A", "K"])
        # Compute a bid based on hand strength.
        if has5 or topCount >= 2:
            bid = 20
        elif topCount == 1:
            bid = 15
        else:
            bid = 0
        if bid == 20 and random.random() < 0.3:
            bid = 25
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
                    self.biddingMessage = "Dealer automatically bid 15. Please select the trump suit. Dealer: " + self.dealer
                    self.phase = "trump"
                else:
                    if player_bid == 0:
                        # Player passed; force computer's bid to minimum 15.
                        self.bidder = comp_id
                        self.bid = 15
                        _, comp_trump = self.computer_bid(comp_id)
                        self.trump_suit = comp_trump
                        self.biddingMessage = f"{comp_id} wins the bid with 15 and selects {comp_trump} as trump."
                        self.phase = "draw"
                    else:
                        if player_bid != 0 and player_bid != comp_bid + 5:
                            self.biddingMessage = f"As dealer, you must pass or bid {comp_bid + 5}."
                            return self.to_dict()
                        self.bidder = "player"
                        self.bid = player_bid
                        self.biddingMessage = f"Player wins the bid with {player_bid}. Please select the trump suit."
                        self.phase = "trump"
            else:
                if player_bid == 0 and comp_bid == 0:
                    self.bidder = comp_id
                    self.bid = 15
                    self.bidHistory["player"] = "Passed"
                    self.bidHistory[comp_id] = "Passed"
                    self.trump_suit = self.computer_bid(comp_id)[1]
                    self.biddingMessage = f"Both passed. {comp_id} wins the bid with 15 and selects trump {self.trump_suit}."
                    self.phase = "draw"
                elif player_bid != 0 and player_bid >= comp_bid:
                    self.bidder = "player"
                    self.bid = player_bid
                    self.bidHistory[comp_id] = "Passed"
                    self.biddingMessage = f"Player wins the bid with {player_bid}. Please select the trump suit."
                    self.phase = "trump"
                else:
                    self.bidder = comp_id
                    self.bid = comp_bid
                    _, comp_trump = self.computer_bid(comp_id)
                    self.trump_suit = comp_trump
                    self.biddingMessage = f"{comp_id} wins the bid with {comp_bid} and selects trump {comp_trump}."
                    self.phase = "draw"
            self.currentTurn = self.bidder
        return self.to_dict()

    def select_trump(self, suit):
        if self.phase == "trump":
            self.trump_suit = suit
            self.biddingMessage = f"Trump is set to {suit}."
            if self.bidder == "player":
                self.phase = "kitty"
            else:
                self.phase = "draw"
        return

    def confirm_kitty(self, keptIndices):
        if self.bidder == "player":
            original_count = len(self.players["player"]["hand"])
            self.combinedHand = self.players["player"]["hand"] + self.kitty
            selected = []
            for i in keptIndices:
                if i < len(self.combinedHand):
                    card = self.combinedHand[i]
                    card.selected = True
                    selected.append(card)
            if not any(i < original_count for i in keptIndices):
                selected.insert(0, self.players["player"]["hand"][0])
            self.players["player"]["hand"] = selected
            self.biddingMessage = "Kitty selection confirmed. Proceeding to draw phase."
            self.phase = "draw"
            self.combinedHand = []
        else:
            self.phase = "draw"
        return self.to_dict()

    def confirm_draw(self, keptIndices=None):
        if keptIndices is None or len(keptIndices) == 0:
            kept_cards = self.players["player"]["hand"]
        else:
            kept_cards = []
            for i in keptIndices:
                if i < len(self.players["player"]["hand"]):
                    card = self.players["player"]["hand"][i]
                    card.selected = True
                    kept_cards.append(card)
            if len(kept_cards) == 0:
                kept_cards = self.players["player"]["hand"]
        self.players["player"]["hand"] = kept_cards
        while len(self.players["player"]["hand"]) < 5 and len(self.deck.cards) > 0:
            self.players["player"]["hand"].append(self.deck.deal(1)[0])
        for card in self.players["player"]["hand"]:
            card.selected = False
        for p in self.players:
            if p != "player":
                current_hand = self.players[p]["hand"]
                trump_cards = [card for card in current_hand if is_trump(card, self.trump_suit)]
                drawn = 5 - len(trump_cards)
                for _ in range(drawn):
                    if len(self.deck.cards) > 0:
                        trump_cards.append(self.deck.deal(1)[0])
                self.players[p]["hand"] = trump_cards
                self.computerDrawCounts[p] = drawn
                timestamp = time.strftime("%H:%M:%S")
                self.gameNotes.append(f"{timestamp} - {p} drew {drawn} card(s) in draw phase.")
        self.biddingMessage = "Draw complete. Proceeding to trick play."
        self.phase = "trick"
        self.currentTurn = self.bidder
        if self.currentTurn != "player":
            try:
                self.auto_play()
            except Exception as e:
                self.gameNotes.append(f"Auto play error: {str(e)}")
        return self.to_dict()

    def validate_move(self, player, card):
        if not self.currentTrick:
            return True, ""
        lead_card = self.currentTrick[0]["card"]
        lead_suit = lead_card.suit
        if is_trump(lead_card, self.trump_suit):
            if not is_trump(card, self.trump_suit):
                trump_in_hand = [c for c in self.players[player]["hand"] if is_trump(c, self.trump_suit)]
                if trump_in_hand:
                    return False, "Invalid move: When a trump is led, you must play a trump card if you have one."
                else:
                    return True, ""
            else:
                trump_in_hand = [c for c in self.players[player]["hand"] if is_trump(c, self.trump_suit)]
                if trump_in_hand:
                    trump_in_hand.sort(key=lambda c: get_trump_value(c, self.trump_suit), reverse=True)
                    top_three = trump_in_hand[:3]
                    if not any(card.rank == tc.rank and card.suit == tc.suit for tc in top_three):
                        return False, "Invalid move: You must play one of your top 3 trump cards."
                return True, ""
        if card.suit == lead_suit or is_trump(card, self.trump_suit):
            return True, ""
        if any(c.suit == lead_suit for c in self.players[player]["hand"]):
            return False, "Invalid move: You must follow suit or play a valid trump card."
        return True, ""
    
    def play_card(self, player, cardText):
        hand = self.players[player]["hand"]
        index = None
        for i, card in enumerate(hand):
            if card.text == cardText:
                index = i
                break
        if index is None:
            return self.to_dict()  # Card not found; return current state.
        card = hand.pop(index)
        card.selected = True
        self.currentTrick.append({"player": player, "card": card})
        timestamp = time.strftime("%H:%M:%S")
        self.gameNotes.append(f"{timestamp} - {player} played {card}")
        self.currentTurn = self.next_player(player)
        try:
            self.auto_play()
        except Exception as e:
            self.gameNotes.append(f"Auto play error: {str(e)}")
        if len(self.currentTrick) == len(self.player_order):
            self.finish_trick()
        return self.to_dict()

    def auto_play(self):
        while self.currentTurn != "player" and len(self.currentTrick) < len(self.player_order):
            time.sleep(0.3)  # Slight delay to simulate computer thinking.
            available = self.players[self.currentTurn]["hand"]
            if not available:
                break
            if self.currentTrick:
                lead_card = self.currentTrick[0]["card"]
                if is_trump(lead_card, self.trump_suit):
                    trump_cards = [card for card in available if is_trump(card, self.trump_suit)]
                    if trump_cards:
                        available = trump_cards
                else:
                    suit_cards = [card for card in available if card.suit == lead_card.suit]
                    if suit_cards:
                        available = suit_cards
            valid_moves = []
            for card in available:
                valid, _ = self.validate_move(self.currentTurn, card)
                if valid:
                    valid_moves.append(card)
            if valid_moves:
                available = valid_moves
            idx = random.randrange(len(available))
            card_to_play = available[idx]
            self.play_card(self.currentTurn, card_to_play.text)
        return

    def finish_trick(self):
        # If the last card played is by the computer, delay to let the player see it.
        if self.currentTrick and self.currentTrick[-1]["player"] != "player":
            time.sleep(0.5)
        winner = self.evaluate_trick(self.currentTrick)
        timestamp = time.strftime("%H:%M:%S")
        trick_summary = f"{timestamp} - " + ", ".join(f"{entry['player']} played {entry['card']}" for entry in self.currentTrick)
        trick_summary += f". Winner: {winner}."
        self.gameNotes.append(trick_summary)
        self.trickLog.append(trick_summary)
        self.lastTrick = self.currentTrick.copy()  # For display in the Trick Area
        self.players[winner]["tricks"].append(self.currentTrick.copy())
        for entry in self.currentTrick:
            if is_trump(entry["card"], self.trump_suit):
                self.trumpCardsPlayed.append((entry["player"], entry["card"]))
        self.currentTrick = []
        self.phase = "trickComplete"
        self.currentTurn = winner if winner is not None else "player"
        self.trick_count += 1
        if self.trick_count >= 5:
            return self.complete_hand()
        return

    def clear_trick(self):
        self.lastTrick = []
        self.phase = "trick"
        if self.currentTurn != "player":
            self.auto_play()
        return self.to_dict()

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
        trump_played = self.trumpCardsPlayed.copy()
        if not trump_played:
            for p in self.players:
                for trick in self.players[p]["tricks"]:
                    for entry in trick:
                        card = entry["card"]
                        if is_trump(card, self.trump_suit):
                            trump_played.append((p, card))
        if trump_played:
            bonus_winner, _ = max(trump_played, key=lambda x: get_trump_value(x[1], self.trump_suit))
        elif self.currentTurn:
            bonus_winner = self.currentTurn
        if bonus_winner:
            points[bonus_winner] += bonus_value
        if self.bidder in points and points[self.bidder] < self.bid:
            points[self.bidder] = -self.bid
        hand_summary_parts = []
        for p in self.players:
            hand_points = points[p]
            new_total = self.players[p]["score"] + hand_points
            label = "Player" if p == "player" else p
            hand_summary_parts.append(f"{label}: {hand_points} (Total: {new_total})")
            self.players[p]["score"] = new_total
        summary = "Hand over. " + " | ".join(hand_summary_parts)
        self.trickLog.append(summary)
        self.handScores.append(summary)
        self.gameNotes.append(summary)
        self.currentTrick = []
        self.lastTrick = []
        if any(self.players[p]["score"] >= 120 for p in self.players):
            self.phase = "finished"
            return self.to_dict()
        else:
            return self.new_hand()

    def new_hand(self):
        current_idx = self.player_order.index(self.dealer)
        self.dealer = self.player_order[(current_idx + 1) % len(self.player_order)]
        self.deal_hands()
        return self.to_dict()

    def to_dict(self):
        state = {
            "gamePhase": self.phase,
            "playerHand": [card.to_dict() for card in self.players["player"]["hand"]],
            "computerHandCount": (len(self.players[self.player_order[1]]["hand"]) if self.mode == "2p" else None),
            "kitty": [card.to_dict() for card in self.kitty],
            "trumpSuit": self.trump_suit if self.phase not in ["bidding"] else None,
            "biddingMessage": self.biddingMessage,
            "bidHistory": self.bidHistory,
            "currentTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.currentTrick],
            "lastTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.lastTrick],
            "trickLog": self.trickLog,
            "scoreboard": {("Player" if p == "player" else p): self.players[p]["score"] for p in self.players},
            "currentTurn": self.currentTurn if self.currentTurn is not None else "player",
            "dealer": self.dealer,
            "gameNotes": self.gameNotes,
            "handScores": self.handScores,
            "mode": self.mode,
            "bidder": self.bidder
        }
        if self.phase == "kitty" and self.bidder == "player":
            state["originalHand"] = [card.to_dict() for card in self.players["player"]["hand"]]
            state["kitty"] = [card.to_dict() for card in self.kitty]
        if self.phase == "draw":
            state["drawHand"] = [card.to_dict() for card in self.players["player"]["hand"]]
            if self.mode == "2p":
                comp = self.player_order[1]
                state["computerDrawCount"] = self.computerDrawCounts.get(comp, 0)
            else:
                state["computerDrawCounts"] = self.computerDrawCounts
        return state
