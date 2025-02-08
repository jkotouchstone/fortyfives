import random

# ---------------------------
# Card and Deck Classes
# ---------------------------

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
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards to deal.")
        return [self.cards.pop() for _ in range(num_cards)]

# ---------------------------
# Ranking Definitions
# ---------------------------
# Trump ranking orders for each trump suit.
TRUMP_RANKINGS = {
    "Diamonds": ["5", "J", "A♥", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "Hearts":   ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "Clubs":    ["5", "J", "A♥", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"],
    "Spades":   ["5", "J", "A♥", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"]
}

# Off-suit ranking orders for cards that are not trump.
OFFSUIT_RANKINGS = {
    "Diamonds": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "Hearts":   ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "Clubs":    ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "Spades":   ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
}

# ---------------------------
# Helper Functions for Trick Evaluation
# ---------------------------

def is_trump(card, trump_suit):
    """
    A card is trump if its suit matches the trump suit or if it is the Ace of Hearts.
    (Ace of Hearts is always considered part of the trump suit.)
    """
    if card.suit == trump_suit:
        return True
    if card.rank == "A" and card.suit == "Hearts":
        return True
    return False

def get_trump_value(card, trump_suit):
    """
    Return a numeric value for a trump card based on the trump ranking order.
    The higher the value, the stronger the card. (Here we invert the index so that a lower index means a stronger card.)
    """
    ranking = TRUMP_RANKINGS[trump_suit]
    # For Ace of Hearts, choose the appropriate token.
    if card.rank == "A" and card.suit == "Hearts":
        token = "A" if trump_suit == "Hearts" else "A♥"
    else:
        token = card.rank
    return len(ranking) - ranking.index(token)

def get_offsuit_value(card):
    """
    Return a numeric value for an off-suit card using the off-suit ranking order.
    Higher value means a stronger card.
    """
    ranking = OFFSUIT_RANKINGS[card.suit]
    return len(ranking) - ranking.index(card.rank)

# ---------------------------
# Game Class
# ---------------------------

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = {
            "player": {"hand": [], "score": 0, "tricks": []},
            "computer": {"hand": [], "score": 0, "tricks": []}
        }
        self.dealer = "computer"
        self.trump_suit = None
        self.current_bid = None
        self.phase = "bidding"
        self.kitty = []
        self.current_trick = []  # List of tuples: (player, card)
        self.winner = None  # "player" or "computer" after bidding

    def deal_hands(self):
        """Deals hands to both players and the kitty."""
        self.deck = Deck()
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.trump_suit = None
        self.current_bid = None
        self.current_trick = []
        self.winner = None

    def computer_bid(self):
        """
        Evaluates the computer's hand strength using the following logic:
        
        - If the hand contains a 5, bid 20 (since even a lone 5 guarantees about 10 points if trump is selected).
        - Otherwise, if the hand contains at least two key cards (from among Jack, Ace of Hearts, a non‑Hearts Ace, or King), bid 20.
        - If there is only one key card (and no 5), bid 15.
        - Otherwise, pass by bidding 0.
        
        Also, returns a preferred trump suit, chosen as the suit in which the computer holds the most cards.
        """
        hand = self.players["computer"]["hand"]

        # Check for key cards.
        has_5 = any(card.rank == "5" for card in hand)
        has_jack = any(card.rank == "J" for card in hand)
        has_ace_hearts = any(card.rank == "A" and card.suit == "Hearts" for card in hand)
        has_nonheart_ace = any(card.rank == "A" and card.suit != "Hearts" for card in hand)
        has_king = any(card.rank == "K" for card in hand)

        # Count key cards (excluding the 5, which is decisive)
        top_count = 0
        if has_jack:
            top_count += 1
        if has_ace_hearts:
            top_count += 1
        if has_nonheart_ace:
            top_count += 1
        if has_king:
            top_count += 1

        if has_5:
            bid_value = 20
        elif top_count >= 2:
            bid_value = 20
        elif top_count == 1:
            bid_value = 15
        else:
            bid_value = 0

        # Determine preferred trump suit by counting cards in each suit.
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        suit_counts = {s: 0 for s in suits}
        for card in hand:
            suit_counts[card.suit] += 1
        best_suit = max(suit_counts, key=suit_counts.get)

        return bid_value, best_suit

    def evaluate_trick(self, trick):
        """
        Given a trick (a list of (player, card) tuples in play order), determine who wins the trick.
        
        Rules applied:
          1. If one or more trump cards are played, the highest trump wins (using the trump ranking).
          2. If no trump cards are played, the highest card in the lead suit wins (using the off-suit ranking).
        """
        trump = self.trump_suit
        # First, check for trump cards.
        trump_cards = [(player, card) for player, card in trick if is_trump(card, trump)]
        if trump_cards:
            winning_player, winning_card = max(trump_cards, key=lambda x: get_trump_value(x[1], trump))
            return winning_player, winning_card
        else:
            # No trump cards played; follow the suit of the first card (lead suit).
            lead_suit = trick[0][1].suit
            lead_cards = [(player, card) for player, card in trick if card.suit == lead_suit]
            if lead_cards:
                winning_player, winning_card = max(lead_cards, key=lambda x: get_offsuit_value(x[1]))
                return winning_player, winning_card
            # Fallback: return the first play (should not occur in legal play).
            return trick[0]
