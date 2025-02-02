# game_logic.py
import random

###############################################################################
#                    CARD RANK & LOOKUP DICTIONARIES
###############################################################################
# (These dictionaries define the trump ranking. Note: Ace of Hearts is always trump.
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

# For off-suit cards, we use a standard order for evaluating a trick when no trump is played.
STANDARD_ORDER = {"2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "10":10, "J":11, "Q":12, "K":13, "A":14}

def get_card_rank(card_str: str, trump_suit: str) -> int:
    """Return numeric rank for card_str under the declared trump suit.
       If the card is trump (its suit equals trump_suit or it is 'A of Hearts'), use the trump dictionary.
       Otherwise, use standard order based on the card’s rank.
    """
    if not trump_suit:
        return STANDARD_ORDER.get(card_str.split(" of ")[0], 0)
    # Check if card is trump
    if "A of Hearts" in card_str:
        return TRUMP_HEARTS.get("A of Hearts", 0)
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return 0
    rank, suit = parts
    if suit == trump_suit:
        if trump_suit == "Diamonds":
            return TRUMP_DIAMONDS.get(card_str, 0)
        elif trump_suit == "Hearts":
            return TRUMP_HEARTS.get(card_str, 0)
        elif trump_suit == "Clubs":
            return TRUMP_CLUBS.get(card_str, 0)
        elif trump_suit == "Spades":
            return TRUMP_SPADES.get(card_str, 0)
    # Otherwise, off-suit: use standard order
    return STANDARD_ORDER.get(rank, 0)

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str: str) -> str:
    """Convert '10 of Hearts' to the appropriate image URL for deckofcardsapi."""
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
#                             GAME CLASSES
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
        self.dealer = 1  # 0: user, 1: comp
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # 0: user, 1: comp
        self.bid = 0
        self.leading_player = None  # who leads the next trick
        self.highest_card_played = None
        self.highest_card_owner = None
        self.last_played_cards = []  # List of (player_name, card_str, card_img)
        self.kitty_revealed = False
        self.bidding_done = False
        self.game_over = False

    def rotate_dealer(self):
        self.dealer = 1 - self.dealer

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
        Bidding logic:
          - Valid bids: 15, 20, 25, 30 (or 0 for pass)
          - For this implementation, if the user bids 15, they win the bid.
          - Otherwise, the computer wins with a bid of 20.
          - (You can expand this logic later for proper auction.)
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
            # Computer auto-selects trump based on its hand:
            comp = self.players[1]
            suit_counts = {"Hearts": 0, "Diamonds": 0, "Clubs": 0, "Spades": 0}
            for c in comp.hand:
                suit_counts[c.suit] += 1
            self.trump_suit = max(suit_counts, key=suit_counts.get)
            return "Computer outbid you with 20. Computer wins the bid. Trump is set to " + self.trump_suit + "."

    def set_trump(self, suit=None):
        """
        If user is bidder, set trump to chosen suit.
        Otherwise, trump remains as chosen by computer.
        """
        if self.bid_winner == 0:
            self.trump_suit = suit
        # Else, do nothing (already set).

    def attach_kitty_user(self):
        """If user is bidder, reveal the kitty so they can choose cards to add."""
        self.kitty_revealed = True

    def discard_comp(self) -> int:
        """
        Computer discards up to 4 non-trump cards.
        It keeps any card of trump suit or the Ace of Hearts.
        """
        comp = self.players[1]
        def keep(c):
            return (c.suit == self.trump_suit) or (c.suit == "Hearts" and c.rank == "A")
        to_discard = []
        for c in comp.hand:
            if not keep(c):
                to_discard.append(c)
            if len(to_discard) >= 4:
                break
        count = len(to_discard)
        for c in to_discard:
            comp.hand.remove(c)
        new_cards = self.deck.deal(count)
        comp.hand.extend(new_cards)
        return count

    def discard_user(self, disc_list) -> int:
        """
        User discards the selected cards and draws replacements.
        """
        user = self.players[0]
        removed = []
        for d in disc_list:
            for c in user.hand:
                if str(c) == d:
                    removed.append(c)
                    break
        for c in removed:
            user.hand.remove(c)
        new_cards = self.deck.deal(len(removed))
        user.hand.extend(new_cards)
        return len(removed)

    def both_discard_done_check(self):
        """
        Once both sides have discarded, set the leading player to the bid winner.
        (For simplicity, we assume both discard phases happen via routes.)
        """
        self.leading_player = self.bid_winner

    def record_high_card(self, card_obj, pid):
        rank_val = get_card_rank(str(card_obj), self.trump_suit)
        if self.highest_card_played is None:
            self.highest_card_played = str(card_obj)
            self.highest_card_owner = pid
        else:
            current = get_card_rank(self.highest_card_played, self.trump_suit)
            if rank_val > current:
                self.highest_card_played = str(card_obj)
                self.highest_card_owner = pid

    def evaluate_trick(self, plays) -> int:
        """
        Evaluate a trick.
        'plays' is a list of tuples: (player_id, card_object).
        If any trump card is played (or the Ace of Hearts), choose the highest trump.
        Otherwise, choose the highest card in the suit that was led.
        """
        led_suit = plays[0][1].suit
        trump_plays = []
        for pid, card in plays:
            # A of Hearts is always trump.
            if card.suit == self.trump_suit or str(card) == "A of Hearts":
                trump_plays.append((pid, card))
        if trump_plays:
            winner = trump_plays[0]
            for pid, card in trump_plays:
                if get_card_rank(str(card), self.trump_suit) > get_card_rank(str(winner[1]), self.trump_suit):
                    winner = (pid, card)
            return winner[0]
        else:
            # Evaluate only cards in the led suit.
            best = plays[0]
            for pid, card in plays:
                if card.suit == led_suit and off_suit_rank(str(card)) > off_suit_rank(str(best[1])):
                    best = (pid, card)
            return best[0]

    def auto_finalize(self):
        """
        After 5 tricks:
          - Award bonus 5 points to the player who played the highest card.
          - If the bidder’s trick points (5 per trick, plus bonus) are less than their bid, subtract bid.
          - Then rotate dealer, reset hand, and deal new hand if game not over.
        """
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5
        if self.bid_winner is not None:
            bidder = self.players[self.bid_winner]
            trick_points = bidder.tricks_won * 5
            if self.highest_card_owner == self.bid_winner:
                trick_points += 5
            if trick_points < self.bid:
                bidder.score -= self.bid
        if self.players[0].score >= 120 or self.players[1].score >= 120:
            self.game_over = True
        else:
            self.rotate_dealer()
            self.reset_hand()
            self.deal_hands()

    def play_trick_user_lead(self, card_str: str) -> str:
        """
        If the user is leading the trick.
        The user plays a card; then the computer responds.
        """
        if self.game_over:
            return "Game over."
        if self.leading_player != 0:
            return "It is not your turn to lead."
        user = self.players[0]
        chosen = None
        for c in user.hand:
            if str(c) == card_str:
                chosen = c
                break
        if not chosen:
            return "Card not in your hand."
        user.hand.remove(chosen)
        self.last_played_cards = [(user.name, str(chosen), card_to_image_url(str(chosen)))]
        self.record_high_card(chosen, 0)
        # Computer responds
        comp = self.players[1]
        follow = None
        for c in comp.hand:
            if c.suit == chosen.suit:
                follow = c
                break
        if not follow:
            follow = comp.hand[0]
        comp.hand.remove(follow)
        self.last_played_cards.append((comp.name, str(follow), card_to_image_url(str(follow))))
        self.record_high_card(follow, 1)
        winner = self.evaluate_trick([(0, chosen), (1, follow)])
        self.players[winner].score += 5
        self.players[winner].tricks_won += 1
        self.leading_player = winner
        total_tricks = self.players[0].tricks_won + self.players[1].tricks_won
        if total_tricks >= 5:
            self.auto_finalize()
        return f"You played {chosen}. Computer played {follow}. Winner: {self.players[winner].name}."

    def comp_lead_trick(self) -> str:
        """
        If the computer is leading the trick.
        The computer plays a card; the user must respond.
        """
        if self.game_over:
            return "Game over."
        if self.leading_player != 1:
            return "It is not computer's turn to lead."
        comp = self.players[1]
        comp.hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
        lead = comp.hand.pop(0)
        self.last_played_cards = [(comp.name, str(lead), card_to_image_url(str(lead)))]
        self.record_high_card(lead, 1)
        return f"Computer leads with {lead}."

    def respond_to_comp_lead(self, user_card_str: str) -> str:
        """
        If the computer has led, the user responds with a card.
        """
        if self.game_over:
            return "Game over."
        user = self.players[0]
        chosen = None
        for c in user.hand:
            if str(c) == user_card_str:
                chosen = c
                break
        if not chosen:
            return "Card not in your hand."
        user.hand.remove(chosen)
        self.last_played_cards.append((user.name, str(chosen), card_to_image_url(str(chosen))))
        self.record_high_card(chosen, 0)
        winner = self.evaluate_trick([(1, self.last_played_cards[0][1]), (0, chosen)])
        self.players[winner].score += 5
        self.players[winner].tricks_won += 1
        self.leading_player = winner
        total_tricks = self.players[0].tricks_won + self.players[1].tricks_won
        if total_tricks >= 5:
            self.auto_finalize()
        return f"Computer led {self.last_played_cards[0][1]}, you played {chosen}. Winner: {self.players[winner].name}."

def off_suit_rank(card_str: str) -> int:
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return 0
    rank, _ = parts
    return STANDARD_ORDER.get(rank, 0)
