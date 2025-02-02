import random

###############################################################################
#                       CARD RANK & LOOKUP DICTIONARIES
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
    if not trump_suit:
        return 0
    if trump_suit == "Diamonds":
        if card_str in TRUMP_DIAMONDS:
            return TRUMP_DIAMONDS[card_str]
        if card_str.endswith("Hearts"):
            return OFFSUIT_HEARTS.get(card_str, 0)
        elif card_str.endswith("Clubs"):
            return OFFSUIT_CLUBS.get(card_str, 0)
        elif card_str.endswith("Spades"):
            return OFFSUIT_SPADES.get(card_str, 0)
        return 0
    elif trump_suit == "Hearts":
        if card_str in TRUMP_HEARTS:
            return TRUMP_HEARTS[card_str]
        if card_str.endswith("Diamonds"):
            return OFFSUIT_DIAMONDS.get(card_str, 0)
        elif card_str.endswith("Clubs"):
            return OFFSUIT_CLUBS.get(card_str, 0)
        elif card_str.endswith("Spades"):
            return OFFSUIT_SPADES.get(card_str, 0)
        return 0
    elif trump_suit == "Clubs":
        if card_str in TRUMP_CLUBS:
            return TRUMP_CLUBS[card_str]
        if card_str.endswith("Diamonds"):
            return OFFSUIT_DIAMONDS.get(card_str, 0)
        elif card_str.endswith("Hearts"):
            return OFFSUIT_HEARTS.get(card_str, 0)
        elif card_str.endswith("Spades"):
            return OFFSUIT_SPADES.get(card_str, 0)
        return 0
    elif trump_suit == "Spades":
        if card_str in TRUMP_SPADES:
            return TRUMP_SPADES[card_str]
        if card_str.endswith("Diamonds"):
            return OFFSUIT_DIAMONDS.get(card_str, 0)
        elif card_str.endswith("Hearts"):
            return OFFSUIT_HEARTS.get(card_str, 0)
        elif card_str.endswith("Clubs"):
            return OFFSUIT_CLUBS.get(card_str, 0)
        return 0
    return 0

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str: str) -> str:
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return card_back_url()
    rank, suit = parts
    rank_map = {
        "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
        "10": "0", "J": "J", "Q": "Q", "K": "K", "A": "A"
    }
    if rank not in rank_map:
        return card_back_url()
    return f"https://deckofcardsapi.com/static/img/{rank_map[rank]}{suit[0].upper()}.png"

###############################################################################
#                             GAME CLASSES                                    #
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
    def deal(self, n):
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0
    def add_to_hand(self, cards):
        self.hand.extend(cards)

class Game:
    def __init__(self):
        self.players = [Player("You"), Player("Computer")]
        self.dealer = 1  # 0: user, 1: computer
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = None  # who leads the next trick
        self.highest_card_played = None
        self.highest_card_owner = None
        self.last_played_cards = []
        self.kitty_revealed = False
        self.bidding_done = False
        self.game_over = False

    def reset_hand(self):
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = None
        self.highest_card_played = None
        self.highest_card_owner = None
        self.last_played_cards = []
        self.kitty_revealed = False
        self.bidding_done = False
        self.game_over = False
        for p in self.players:
            p.hand = []
            p.tricks_won = 0

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand = []
        self.kitty = []
        first_bidder = 0 if self.dealer == 1 else 1
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self, bid_val: int) -> str:
        """
        Minimal bidding logic:
        - If user bids 15, let user win the bid.
        - Otherwise, let computer win with bid 20 and set trump to "Hearts".
        (Expand this as needed.)
        """
        if bid_val == 15:
            self.bid_winner = 0
            self.bid = 15
            self.bidding_done = True
            return "You bid 15 and win the bid."
        else:
            self.bid_winner = 1
            self.bid = 20
            self.bidding_done = True
            # For demo, computer automatically sets trump to Hearts.
            self.trump_suit = "Hearts"
            return "Computer outbid you with 20. Computer wins the bid. Trump is set to Hearts."

    # For this minimal demo, we leave other methods unimplemented.
    def set_trump(self, suit=None):
        # If user wins bid, set trump to suit provided; else use computer's automatic trump.
        if self.bid_winner == 0:
            self.trump_suit = suit
        # Otherwise, trump is already set by bidding logic.
    
    def attach_kitty_user(self):
        self.kitty_revealed = True

    def discard_comp(self):
        # Minimal: computer discards 1 card (if available) from its hand.
        comp = self.players[1]
        if comp.hand:
            card = comp.hand.pop(0)
            new_card = self.deck.deal(1)[0]
            comp.hand.append(new_card)
            return 1
        return 0

    def discard_user(self, discard_list):
        # Minimal: remove any matching cards from user.hand and draw replacements.
        user = self.players[0]
        removed = []
        for d in discard_list:
            for c in user.hand:
                if str(c) == d:
                    removed.append(c)
                    break
        for c in removed:
            user.hand.remove(c)
        new_cards = self.deck.deal(len(removed))
        user.hand.extend(new_cards)
        return len(removed)

    def record_high_card(self, card_obj, pid):
        # For demo, simply store the first card.
        if self.highest_card_played is None:
            self.highest_card_played = str(card_obj)
            self.highest_card_owner = pid

    def evaluate_trick(self, plays):
        # Minimal: simply return the first player's id.
        return plays[0][0]

    def auto_finalize(self):
        # Minimal finalization: award +5 for highest card, then rotate dealer and deal a new hand.
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5
        if self.players[0].score >= 120 or self.players[1].score >= 120:
            self.game_over = True
        else:
            self.rotate_dealer()
            self.reset_hand()
            self.deal_hands()

    # For trick play methods, you’d implement similar minimal logic as needed.
