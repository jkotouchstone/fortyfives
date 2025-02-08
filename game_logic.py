import random

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

# --------------------------
# Ranking orders definitions
# --------------------------

# When a suit is trump, the trump ranking for that suit is used.
# Notice that in trump rankings, the Ace of hearts is “special”:
# if hearts is not the trump suit, A♥ is represented as "A♥" in the ranking list.
TRUMP_RANKINGS = {
    "Diamonds": ["5", "J", "A♥", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "Hearts":   ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "Clubs":    ["5", "J", "A♥", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"],
    "Spades":   ["5", "J", "A♥", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"]
}

# Off-suit ranking orders for cards that are not trump.
# (Recall that A♥ is always trump, so if hearts isn’t trump you never consider it off-suit.)
OFFSUIT_RANKINGS = {
    "Diamonds": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "Hearts":   ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "Clubs":    ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "Spades":   ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
}

# --------------------------
# Helper functions
# --------------------------

def is_trump(card, trump_suit):
    """
    Determines if a card is trump.
    A card is trump if its suit matches the trump suit or if it is the Ace of Hearts (A♥),
    which is always considered part of the trump suit.
    """
    if card.suit == trump_suit:
        return True
    if card.rank == "A" and card.suit == "Hearts":
        return True
    return False

def get_trump_value(card, trump_suit):
    """
    Returns a numeric value for a trump card.
    The higher the value, the stronger the card.
    
    It uses the trump ranking list for the given trump suit. Note that if the trump suit
    is "Hearts", the Ace of hearts is looked up as "A" (since the trump ranking for hearts
    uses "A"), but for any other trump suit, Ace of hearts is represented by "A♥".
    
    The ranking lists are ordered best-to-worst.
    """
    ranking = TRUMP_RANKINGS[trump_suit]
    if card.rank == "A" and card.suit == "Hearts":
        token = "A" if trump_suit == "Hearts" else "A♥"
    else:
        token = card.rank
    # Compute value so that the best card gets the highest number.
    return len(ranking) - ranking.index(token)

def get_offsuit_value(card):
    """
    Returns a numeric value for an off-suit card using the off-suit ranking.
    Higher value means a stronger card.
    """
    ranking = OFFSUIT_RANKINGS[card.suit]
    return len(ranking) - ranking.index(card.rank)

# --------------------------
# Game Class
# --------------------------

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = {
            "player": {"hand": [], "score": 0, "tricks": []},
            "computer": {"hand": [], "score": 0, "tricks": []}
        }
        self.dealer = "computer"
        self.trump_suit = None  # To be set when bidding is complete.
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
        Evaluates the computer's hand strength and returns a bid value along with a preferred trump suit.
        (This remains largely unchanged from your original code.)
        """
        hand = self.players["computer"]["hand"]
        rank_order = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
                      "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        trump_strength = {}
        
        # Sum up basic strength for each suit.
        for suit in suits:
            trump_strength[suit] = sum(rank_order.get(card.rank, 0) for card in hand if card.suit == suit)
        
        best_suit = max(trump_strength, key=trump_strength.get)
        best_strength = trump_strength[best_suit]
        
        # Determine power cards (note that A♥ is special).
        power_cards = {card.rank for card in hand if card.rank in ["5", "J", "A"] or (card.rank == "A" and card.suit == best_suit)}
        has_5 = "5" in power_cards
        has_jack = "J" in power_cards
        has_ace_hearts = any(card.rank == "A" and card.suit == "Hearts" for card in hand)
        has_ace_trump = any(card.rank == "A" and card.suit == best_suit for card in hand)
        power_card_count = sum([has_5, has_jack, has_ace_hearts, has_ace_trump])
        
        # Smart bidding based on power cards.
        if power_card_count >= 2:
            bid_value = 20  # Aggressive bid.
        elif power_card_count == 1:
            bid_value = 15  # Moderate bid.
        elif best_strength >= 35:
            bid_value = 25
        elif best_strength >= 30:
            bid_value = 20
        else:
            bid_value = 0  # Pass.
        
        return bid_value, best_suit

    def evaluate_trick(self, trick):
        """
        Given a trick (a list of (player, card) tuples in play order), determine who wins the trick.
        
        Rules applied:
          1. Any trump card (i.e. a card of the trump suit or A♥) beats any off-suit card.
          2. If one or more trump cards are played, the trump card with the highest value wins.
             (Trump values are determined using the trump ranking order for the current trump suit.)
          3. If no trump cards are played, then only cards matching the lead suit (the suit of the first card)
             are eligible; the highest card (using the off-suit ranking for that suit) wins the trick.
        """
        trump = self.trump_suit
        # First, check for any trump cards.
        trump_cards = [(player, card) for player, card in trick if is_trump(card, trump)]
        if trump_cards:
            winning_player, winning_card = max(trump_cards, key=lambda x: get_trump_value(x[1], trump))
            return winning_player, winning_card
        else:
            # No trump cards played. Only cards following the lead suit count.
            lead_suit = trick[0][1].suit
            lead_cards = [(player, card) for player, card in trick if card.suit == lead_suit]
            if lead_cards:
                winning_player, winning_card = max(lead_cards, key=lambda x: get_offsuit_value(x[1]))
                return winning_player, winning_card
            # Fallback (in case no card follows lead suit; unlikely in legal play).
            return trick[0]

    # Additional methods (such as playing a trick or round) would be implemented here.
