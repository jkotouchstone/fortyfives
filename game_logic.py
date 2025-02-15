import random

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self):
        return {
            "suit": self.suit,
            "rank": self.rank,
            "text": f"{self.rank}{self.suit}"
        }

class Deck:
    def __init__(self):
        suits = ["♥", "♦", "♣", "♠"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(s, r) for s in suits for r in ranks]
        random.shuffle(self.cards)

    def deal(self, num_cards):
        return [self.cards.pop() for _ in range(num_cards)]

class Game:
    def __init__(self, mode="2p", instructional=False):
        self.mode = mode
        self.deck = Deck()
        self.players = {}
        self.trump_suit = None
        self.phase = "bidding"
        self.scoreboard = {}
        self.bid = 0

        if self.mode == "2p":
            self.players = {"player": [], "computer": []}
            self.scoreboard = {"player": 0, "computer": 0}
        else:
            self.players = {"player": [], "cpu1": [], "cpu2": []}
            self.scoreboard = {"player": 0, "cpu1": 0, "cpu2": 0}

        for p in self.players:
            self.players[p] = self.deck.deal(5)

    def validate_move(self, player, card):
        return True  

    def play_card(self, player, cardIndex):
        if player in self.players and 0 <= cardIndex < len(self.players[player]):
            self.players[player].pop(cardIndex)

    def process_bid(self, player_bid):
        strong_trump = sum(1 for card in self.players["computer"] if card.rank in ["J", "A", "K"])
        if strong_trump >= 2:
            self.bid = max(self.bid, 20)  
        else:
            self.bid = max(self.bid, player_bid)

    def to_dict(self):
        return {
            "gamePhase": self.phase,
            "playerHand": [card.to_dict() for card in self.players["player"]],
            "scoreboard": self.scoreboard
        }
