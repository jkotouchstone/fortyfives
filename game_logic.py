# game_logic.py

import random

###############################################################################
#                           CARD RANK & LOOKUP DICT                           #
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

def get_card_rank(card_str, trump_suit):
    """ Returns numeric rank for card_str under trump_suit. """
    if not trump_suit:
        return 0
    # Similar logic as your final code
    # ... Truncated for brevity ...
    return 0

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    """
    '10 of Hearts' => '0H.png'
    """
    parts=card_str.split(" of ")
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

###############################################################################
#                          GAME CLASSES                                       #
###############################################################################
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
    def deal(self,n):
        dealt=self.cards[:n]
        self.cards=self.cards[n:]
        return dealt

class Player:
    def __init__(self,name):
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
        # track discard phases
        self.user_discard_done=False
        self.comp_discard_done=False

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
        self.user_discard_done=False
        self.comp_discard_done=False
        for p in self.players:
            p.hand=[]
            p.tricks_won=0

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand=[]
        self.kitty=[]
        self.user_discard_done=False
        self.comp_discard_done=False
        first_bidder=0 if self.dealer==1 else 1
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self,bid_val):
        """
        If user is first => user picks from [0,15,20,25,30], comp can outbid by +5 or pass.
        If user is second => comp picks random from [0,15,20,25,30], user tries to beat or pass.
        If comp wins => comp picks trump behind scenes, sees kitty.
        """
        if self.game_over:
            return "Game over."
        if self.bidding_done:
            return "Bidding done."

        first_bidder=0 if self.dealer==1 else 1
        msg=""
        if first_bidder==0:
            # user first
            if bid_val==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="You bid 30, you instantly win."
            else:
                comp_options=[]
                if bid_val==0:
                    comp_options=[0,15]
                elif bid_val==15:
                    comp_options=[0,20]
                elif bid_val==20:
                    comp_options=[0,25]
                elif bid_val==25:
                    comp_options=[0,30]
                if not comp_options:
                    self.bid_winner=0
                    self.bid= bid_val if bid_val>0 else 15
                    self.bidding_done=True
                    msg=f"You bid {bid_val}, comp pass => you win."
                else:
                    cchoice=random.choice(comp_options)
                    if cchoice>bid_val:
                        self.bid_winner=1
                        self.bid=cchoice
                        self.bidding_done=True
                        msg=f"Computer outbid you with {cchoice}."
                    else:
                        self.bid_winner=self.dealer
                        self.bid=15
                        self.bidding_done=True
                        if self.dealer==1:
                            msg="Both passed => Computer forced 15."
                        else:
                            msg="Both passed => You forced 15."
        else:
            # user second => comp random
            cFirst=random.choice([0,15,20,25,30])
            if cFirst==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="Computer bids 30 instantly."
            else:
                if bid_val>cFirst:
                    self.bid_winner=1
                    self.bid=bid_val
                    self.bidding_done=True
                    msg=f"Computer bid {cFirst}, you outbid => you win."
                elif bid_val==cFirst and cFirst>0:
                    self.bid_winner=1
                    self.bid=bid_val
                    self.bidding_done=True
                    msg=f"Computer bid {cFirst}, you matched => you win."
                else:
                    self.bid_winner=0
                    self.bid= cFirst if cFirst>0 else 15
                    self.bidding_done=True
                    if cFirst>0:
                        msg=f"Computer bid {cFirst}, you didn't beat => comp wins."
                    else:
                        msg="Computer pass, you pass => forced 15 to comp."

        if self.bidding_done:
            if self.bid_winner==1:
                # comp picks trump
                self.set_trump(None)
                # comp sees kitty
                self.players[1].hand.extend(self.kitty)
                self.kitty=[]
        return msg

    def set_trump(self, suit=None):
        if self.bid_winner==1 and self.dealer==1:
            # comp picks auto
            comp_hand=self.players[1].hand
            suits={"Hearts":0,"Diamonds":0,"Clubs":0,"Spades":0}
            for c in comp_hand:
                suits[c.suit]+=1
            self.trump_suit=max(suits,key=suits.get)
        else:
            self.trump_suit=suit

    def attach_kitty_user(self):
        """ If user is bidder => reveal kitty. """
        self.kitty_revealed=True

    def discard_comp(self):
        """ comp discards up to 4 """
        comp=self.players[1]
        def keepTest(c):
            return (c.suit==self.trump_suit) or (c.suit=="Hearts" and c.rank=="A")
        toDiscard=[]
        for c in comp.hand:
            if not keepTest(c):
                toDiscard.append(c)
            if len(toDiscard)>=4:
                break
        discCount=len(toDiscard)
        for c in toDiscard:
            comp.hand.remove(c)
        new_cards=self.deck.deal(discCount)
        comp.hand.extend(new_cards)
        self.comp_discard_done=True
        return discCount

    def discard_user(self, discList):
        user=self.players[0]
        removed=[]
        for d in discList:
            for c in user.hand:
                if str(c)==d:
                    removed.append(c)
                    break
        for c in removed:
            user.hand.remove(c)
        new_cards=self.deck.deal(len(removed))
        user.hand.extend(new_cards)
        self.user_discard_done=True
        return len(removed)

    def both_discard_done_check(self):
        # if user_discard_done & comp_discard_done => leading_player = self.bid_winner
        if self.user_discard_done and self.comp_discard_done:
            self.leading_player=self.bid_winner

    def record_high_card(self, card_obj, pid):
        # see your final logic
        pass

    def evaluate_trick(self, plays):
        pass

    def auto_finalize(self):
        pass

    # Then your trick-play methods, e.g. user leads or comp leads, omitted for brevity.

###############################################################################
#  End of game_logic.py
###############################################################################
