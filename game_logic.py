# game_logic.py
import random

###############################################################################
#                      CARD RANK & LOOKUP DICTIONARIES                        #
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

def get_card_rank(card_str:str, trump_suit:str) -> int:
    """Return numeric rank for card_str under the given trump_suit."""
    if not trump_suit:
        return 0
    # If statements referencing TRUMP_* or OFFSUIT_* dicts
    # Ace of Hearts => 198 rank if it's in the dictionary, etc.
    # (Truncated for brevity)
    return 0

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str:str) -> str:
    parts = card_str.split(" of ")
    if len(parts)!=2:
        return card_back_url()
    rank, suit=parts
    rank_map={
      "2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9",
      "10":"0","J":"J","Q":"Q","K":"K","A":"A"
    }
    if rank not in rank_map:
        return card_back_url()
    rank_code=rank_map[rank]
    suit_code=suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

class Card:
    def __init__(self,suit,rank):
        self.suit=suit
        self.rank=rank
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        suits=["Hearts","Diamonds","Clubs","Spades"]
        ranks=["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
        self.cards=[Card(s,r) for s in suits for r in ranks]
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self,n:int):
        dealt=self.cards[:n]
        self.cards=self.cards[n:]
        return dealt

class Player:
    def __init__(self,name:str):
        self.name=name
        self.hand=[]
        self.score=0
        self.tricks_won=0
    def add_to_hand(self,cards):
        self.hand.extend(cards)

class Game:
    def __init__(self):
        self.players=[Player("You"), Player("Computer")]
        self.dealer=1
        self.deck=Deck()
        self.kitty=[]
        self.trump_suit=None
        self.bid_winner=None
        self.bid=0
        self.leading_player=None
        self.highest_card_played=None
        self.highest_card_owner=None
        self.last_played_cards=[]
        self.kitty_revealed=False
        self.bidding_done=False
        self.game_over=False

    def rotate_dealer(self):
        self.dealer=1-self.dealer

    def reset_hand(self):
        self.deck=Deck()
        self.kitty=[]
        self.trump_suit=None
        self.bid_winner=None
        self.bid=0
        self.leading_player=None
        self.highest_card_played=None
        self.highest_card_owner=None
        self.last_played_cards=[]
        self.kitty_revealed=False
        self.bidding_done=False
        self.game_over=False
        for p in self.players:
            p.hand=[]
            p.tricks_won=0

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand=[]
        self.kitty=[]
        first_bidder=0 if self.dealer==1 else 1
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self,bid_val:int):
        """
        Bidding logic with +5 increments. 
        If computer wins => computer picks trump behind the scenes.
        If user wins => user picks trump from the front-end route.
        """
        #  fill in the final logic from your single-file code
        return f"(Bidding logic result, e.g. user bid {bid_val})"

    def set_trump(self, suit=None):
        """
        If comp is bidder & comp is also dealer => picks from comp's hand. 
        Otherwise, use suit param from user.
        """
        pass

    def attach_kitty_user(self):
        """If user is bidder => reveal kitty to user."""
        self.kitty_revealed=True

    def record_high_card(self, card_obj, pid):
        """Check if this card is highest so far."""
        pass

    def discard_comp(self):
        """Computer discards up to 4 from non-trump suits. 
        Return how many it discarded so we can show in the log.
        """
        return 0

    def discard_user(self, discList):
        """User discards up to 4. Return how many. """
        return 0

    def evaluate_trick(self, plays):
        pass

    def auto_finalize(self):
        pass

    # Additional methods for leading, responding, etc. omitted for brevity.

