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
        return [self.cards.pop() for _ in range(num_cards)]

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
        self.leading_player = None
        self.bidding_active = True
        self.trick_play_active = False
        self.kitty = []
        self.current_trick = []
        self.discard_phase_active = False

    def deal_hands(self):
        """Deals hands to both players and the kitty."""
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)
        self.bidding_active = True
        self.trick_play_active = False
        self.discard_phase_active = False
        self.trump_suit = None

    def get_state(self):
        """Returns the current game state."""
        return {
            "your_cards": [{"name": str(card), "img": self.get_card_image(card)} for card in self.players["player"]["hand"]],
            "computer_count": len(self.players["computer"]["hand"]),
            "kitty_count": len(self.kitty),
            "total_your": self.players["player"]["score"],
            "total_comp": self.players["computer"]["score"],
            "trump_suit": self.trump_suit,
            "dealer": self.dealer,
            "bidding_active": self.bidding_active,
            "trick_play_active": self.trick_play_active,
            "discard_phase_active": self.discard_phase_active,
            "card_back": "https://deckofcardsapi.com/static/img/back.png"
        }

    def get_card_image(self, card):
        """Generates the URL for a card's image."""
        rank_code = "0" if card.rank == "10" else card.rank[0]
        suit_code = card.suit[0].upper()
        return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

    def process_bid(self, player, bid_val):
        """Processes a player's or computer's bid."""
        if not self.bidding_active:
            return "Bidding is not active."

        if player == "player":
            if self.curren
