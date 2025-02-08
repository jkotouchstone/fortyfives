import random

# ---------------------------
# Card and Deck Classes
# ---------------------------
class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g. "♥", "♦", "♣", "♠"
        self.rank = rank  # e.g. "2", "3", …, "10", "J", "Q", "K", "A"

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self):
        return {"suit": self.suit, "rank": self.rank}

class Deck:
    def __init__(self):
        suits = ["♥", "♦", "♣", "♠"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        # Optionally add one joker if needed:
        # self.cards.append(Card("Joker", "Joker"))
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
    # The Ace of Hearts is always considered trump.
    if card.suit == "♥" and card.rank == "A":
        return True
    return False

def get_trump_value(card, trump_suit):
    ranking = TRUMP_RANKINGS[trump_suit]
    # Higher numeric value means stronger card.
    return len(ranking) - ranking.index(card.rank)

def get_offsuit_value(card):
    ranking = OFFSUIT_RANKINGS[card.suit]
    return len(ranking) - ranking.index(card.rank)

# ---------------------------
# Game Class with Score and Hand Advancement
# ---------------------------
class Game:
    def __init__(self, mode="2p", instructional=False):
        self.mode = mode
        self.instructional = instructional
        self.deck = None
        # Each player has a hand, tricks won, and a total score.
        self.players = {
            "player": {"hand": [], "tricks": [], "score": 0},
            "computer": {"hand": [], "tricks": [], "score": 0}
        }
        self.kitty = []
        self.trump_suit = None
        self.phase = "bidding"  # phases: bidding, trump, kitty, draw, trick, finished
        self.biddingMessage = ""
        self.trickCards = []  # Cards played in the current trick
        self.trickLog = []    # Log of completed tricks
        self.currentTurn = "player"  # Whose turn during trick play: "player" or "computer"
        self.bidder = None  # Who won the bid ("player" or "computer")
        self.bid = 0        # The winning bid value
        self.deal_hands()

    def deal_hands(self):
        self.deck = Deck()
        # For simplicity we deal 5 cards per player.
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        # Deal 3 cards to the kitty.
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.biddingMessage = "Place your bid."
        # Clear trick logs for a new hand.
        self.trickLog = []
        self.trickCards = []

    def computer_bid(self):
        # Simple bidding strategy based on key cards.
        hand = self.players["computer"]["hand"]
        has5 = any(card.rank == "5" for card in hand)
        topCount = sum(1 for card in hand if card.rank in ["J", "A", "K"])
        bid = 20 if has5 or topCount >= 2 else (15 if topCount == 1 else 0)
        # Choose preferred trump as the suit with the most cards.
        suit_counts = {}
        for card in hand:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        best_suit = max(suit_counts, key=suit_counts.get)
        return bid, best_suit

    def process_bid(self, player_bid):
        comp_bid, comp_trump = self.computer_bid()
        if player_bid >= comp_bid:
            self.bidder = "player"
            self.bid = player_bid
            self.biddingMessage = f"You win the bid ({player_bid} vs {comp_bid}). Please select trump."
            self.phase = "trump"
        else:
            self.bidder = "computer"
            self.bid = comp_bid
            self.trump_suit = comp_trump
            self.biddingMessage = f"Computer wins the bid ({comp_bid} vs {player_bid}). Computer selects trump."
            self.phase = "kitty"  # Automatically continue
        return

    def select_trump(self, suit):
        if self.phase == "trump":
            self.trump_suit = suit
            self.phase = "kitty"

    def confirm_kitty(self, keptIndices):
        # Combine the player's hand with the kitty.
        combined = self.players["player"]["hand"] + self.kitty
        new_hand = [combined[i] for i in keptIndices if i < len(combined)]
        # Enforce at least one original card and no more than 5 cards.
        if len(new_hand) < 1:
            new_hand = self.players["player"]["hand"][:1]
        if len(new_hand) > 5:
            new_hand = new_hand[:5]
        self.players["player"]["hand"] = new_hand
        self.phase = "draw"

    def confirm_draw(self):
        # Draw cards until the player's hand has 5 cards.
        while len(self.players["player"]["hand"]) < 5 and len(self.deck.cards) > 0:
            self.players["player"]["hand"].append(self.deck.deal(1)[0])
        self.phase = "trick"
        self.currentTurn = "player"

    def play_trick(self, playerCardIndex):
        if self.phase != "trick":
            return
        if playerCardIndex < 0 or playerCardIndex >= len(self.players["player"]["hand"]):
            return

        # --- Player plays a card ---
        player_card = self.players["player"]["hand"].pop(playerCardIndex)
        self.trickCards.append({"player": "player", "card": player_card})

        # --- Computer plays a card (simple strategy: random choice among legal moves) ---
        if self.players["computer"]["hand"]:
            comp_card = random.choice(self.players["computer"]["hand"])
            self.players["computer"]["hand"].remove(comp_card)
            self.trickCards.append({"player": "computer", "card": comp_card})
        else:
            comp_card = None

        # --- Evaluate the trick ---
        winner = self.evaluate_trick(self.trickCards)
        trick_result = f"Trick: You played {player_card}, Computer played {comp_card}. Winner: {winner}"
        self.trickLog.append(trick_result)
        self.players[winner]["tricks"].append(self.trickCards.copy())
        self.trickCards = []

        # --- Check if hand is over ---
        if not self.players["player"]["hand"] or not self.players["computer"]["hand"]:
            self.complete_hand()
        else:
            self.phase = "trick"
            self.currentTurn = "player"

    def evaluate_trick(self, trick):
        if not trick:
            return None
        lead_suit = trick[0]["card"].suit
        # First, check for trump cards.
        trump_plays = [entry for entry in trick if is_trump(entry["card"], self.trump_suit)]
        if trump_plays:
            winner_entry = max(trump_plays, key=lambda x: get_trump_value(x["card"], self.trump_suit))
        else:
            # Otherwise, follow the lead suit.
            follow_plays = [entry for entry in trick if entry["card"].suit == lead_suit]
            if follow_plays:
                winner_entry = max(follow_plays, key=lambda x: get_offsuit_value(x["card"]))
            else:
                winner_entry = trick[0]
        return winner_entry["player"]

    def complete_hand(self):
        # Calculate points for each trick (each trick is worth 5 points)
        points_player = len(self.players["player"]["tricks"]) * 5
        points_computer = len(self.players["computer"]["tricks"]) * 5

        # Give a bonus trick (an extra 5 points) to the player who won the last trick.
        bonus = 5
        last_trick_winner = self.trickLog[-1].split("Winner: ")[-1].strip() if self.trickLog else None
        if last_trick_winner == "player":
            points_player += bonus
        elif last_trick_winner == "computer":
            points_computer += bonus

        # The winning bidder must meet or beat their bid or they lose points equal to the bid.
        if self.bidder == "player":
            if points_player < self.bid:
                points_player = -self.bid
        elif self.bidder == "computer":
            if points_computer < self.bid:
                points_computer = -self.bid

        # Update overall scores.
        self.players["player"]["score"] += points_player
        self.players["computer"]["score"] += points_computer

        # Append a summary message to the trick log.
        hand_summary = (f"Hand over. You scored {points_player} points, Computer scored {points_computer} points. "
                        f"Total: You {self.players['player']['score']} - Computer {self.players['computer']['score']}.")
        self.trickLog.append(hand_summary)

        # Check if someone has reached or exceeded 120 points.
        if self.players["player"]["score"] >= 120 or self.players["computer"]["score"] >= 120:
            self.phase = "finished"
        else:
            # Prepare for next hand.
            self.new_hand()

    def new_hand(self):
        # Reset tricks for each player (but keep overall scores).
        self.players["player"]["tricks"] = []
        self.players["computer"]["tricks"] = []
        # Deal a new hand.
        self.deal_hands()

    def to_dict(self):
        # Return the current game state as a dictionary.
        return {
            "gamePhase": self.phase,
            "playerHand": [card.to_dict() for card in self.players["player"]["hand"]],
            "computerHandCount": len(self.players["computer"]["hand"]),  # Hide computer's cards
            "kitty": [card.to_dict() for card in self.kitty] if self.phase in ["bidding", "kitty"] else [],
            "trumpSuit": self.trump_suit,
            "biddingMessage": self.biddingMessage,
            "trickCards": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.trickCards],
            "trickLog": self.trickLog,
            "scoreboard": f"You: {self.players['player']['score']} | Computer: {self.players['computer']['score']}",
            "feedback": "",
            "combinedHand": [card.to_dict() for card in (self.players["player"]["hand"] + self.kitty)] if self.phase == "kitty" else [],
            "drawHand": [card.to_dict() for card in self.players["player"]["hand"]] if self.phase == "draw" else [],
            "currentTurn": self.currentTurn
        }
