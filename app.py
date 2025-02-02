import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                          CARD RANK LOOKUPS                                  #
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
    """Return numeric rank for card_str under a given trump_suit."""
    if not trump_suit:
        return 0
    if trump_suit=="Diamonds":
        if card_str in TRUMP_DIAMONDS:
            return TRUMP_DIAMONDS[card_str]
        if card_str.endswith("Hearts"):
            return OFFSUIT_HEARTS.get(card_str,0)
        elif card_str.endswith("Clubs"):
            return OFFSUIT_CLUBS.get(card_str,0)
        elif card_str.endswith("Spades"):
            return OFFSUIT_SPADES.get(card_str,0)
        return 0
    elif trump_suit=="Hearts":
        if card_str in TRUMP_HEARTS:
            return TRUMP_HEARTS[card_str]
        if card_str.endswith("Diamonds"):
            return OFFSUIT_DIAMONDS.get(card_str,0)
        elif card_str.endswith("Clubs"):
            return OFFSUIT_CLUBS.get(card_str,0)
        elif card_str.endswith("Spades"):
            return OFFSUIT_SPADES.get(card_str,0)
        return 0
    elif trump_suit=="Clubs":
        if card_str in TRUMP_CLUBS:
            return TRUMP_CLUBS[card_str]
        if card_str.endswith("Diamonds"):
            return OFFSUIT_DIAMONDS.get(card_str,0)
        elif card_str.endswith("Hearts"):
            return OFFSUIT_HEARTS.get(card_str,0)
        elif card_str.endswith("Spades"):
            return OFFSUIT_SPADES.get(card_str,0)
        return 0
    elif trump_suit=="Spades":
        if card_str in TRUMP_SPADES:
            return TRUMP_SPADES[card_str]
        if card_str.endswith("Diamonds"):
            return OFFSUIT_DIAMONDS.get(card_str,0)
        elif card_str.endswith("Hearts"):
            return OFFSUIT_HEARTS.get(card_str,0)
        elif card_str.endswith("Clubs"):
            return OFFSUIT_CLUBS.get(card_str,0)
        return 0
    return 0

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    """
    Convert '10 of Hearts' => '0H.png' for deckofcardsapi.com
    ensuring '10' => '0', suits => first letter uppercase
    """
    parts = card_str.split(" of ")
    if len(parts)!=2:
        return card_back_url()
    rank, suit = parts
    rank_map = {
        "2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9",
        "10":"0","J":"J","Q":"Q","K":"K","A":"A"
    }
    if rank not in rank_map:
        return card_back_url()
    rank_code = rank_map[rank]
    suit_code = suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

class Card:
    def __init__(self, suit, rank):
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

###############################################################################
#                               Game Class                                    #
###############################################################################
class Game:
    def __init__(self):
        self.players=[Player("You"), Player("Computer")]
        self.dealer=1
        self.deck=Deck()
        self.kitty=[]
        self.trump_suit=None
        self.bid_winner=None
        self.bid=0
        self.leading_player=0   # 0 => user, 1 => computer
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
        self.kitty.clear()
        self.trump_suit=None
        self.bid_winner=None
        self.bid=0
        self.leading_player=0
        self.highest_card_played=None
        self.highest_card_owner=None
        self.last_played_cards=[]
        self.kitty_revealed=False
        self.bidding_done=False
        for p in self.players:
            p.hand.clear()
            p.tricks_won=0

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand.clear()
        self.kitty.clear()
        first_bidder = 0 if self.dealer==1 else 1
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self,bid_val):
        """
        The user is either first or second bidder. 
        If first => user picks from [0,15,20,25,30]. Then computer outbids by exactly +5 or pass.
        If second => computer picks random from [0,15,20,25,30], user tries to outbid by +5 or pass.
        If comp wins => comp picks trump, picks kitty, discards up to 4. Then user discards up to 4 if they want. Then first trick => comp leads.
        If user wins => user picks trump, sees kitty, discards, then comp discards up to 4. Then user leads first trick.
        """
        if self.bidding_done or self.game_over:
            return "No bidding possible right now."
        first_bidder = 0 if self.dealer==1 else 1
        msg=""
        if first_bidder==0:
            # user is first
            if bid_val==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="You bid 30, you immediately win the bid."
            else:
                # If user=15 => comp can do pass(0) or 20
                # If user=20 => comp can do pass(0) or 25
                # If user=25 => comp can do pass(0) or 30
                # If user=0 => comp can do pass(0) or 15
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
                    msg=f"You bid {bid_val}, computer passed. You win the bid."
                else:
                    comp_choice=random.choice(comp_options)
                    if comp_choice>bid_val:
                        self.bid_winner=1
                        self.bid=comp_choice
                        self.bidding_done=True
                        msg=f"Computer outbid you with {comp_choice}. Computer wins the bid."
                    else:
                        self.bid_winner=self.dealer
                        self.bid=15
                        self.bidding_done=True
                        if self.dealer==1:
                            msg="Both passed, Computer is dealer => forced 15 to Computer."
                        else:
                            msg="Both passed, You are dealer => forced 15 to You."
        else:
            # user second => comp first => comp picks random
            comp_first = random.choice([0,15,20,25,30])
            if comp_first==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="Computer bids 30, instantly wins the bid."
            else:
                if bid_val>comp_first:
                    self.bid_winner=1
                    self.bid=bid_val
                    self.bidding_done=True
                    msg=f"Computer bid {comp_first}, you outbid with {bid_val}, you win."
                elif (bid_val==comp_first) and comp_first>0:
                    self.bid_winner=1
                    self.bid=bid_val
                    self.bidding_done=True
                    msg=f"Computer bid {comp_first}, you matched => you win the bid."
                else:
                    self.bid_winner=0
                    self.bid= comp_first if comp_first>0 else 15
                    self.bidding_done=True
                    if comp_first>0:
                        msg=f"Computer bid {comp_first}, you didn't beat it => Computer wins."
                    else:
                        msg="Computer passed, you also didn't bid => forced 15 to Computer."

        # If comp wins => comp picks trump => attach kitty => comp discards => user discards => first trick => comp leads
        # If user wins => user picks trump => attach kitty => user discards => comp discards => first trick => user leads
        if self.bidding_done and self.bid_winner==1:
            # comp picks trump
            self.set_trump(None)
            self.attach_kitty()
            # comp discards up to 4, draws
        return msg

    def set_trump(self, suit=None):
        if self.bid_winner==1 and self.dealer==1:
            # comp picks
            comp_hand=self.players[1].hand
            suit_count={"Hearts":0,"Diamonds":0,"Clubs":0,"Spades":0}
            for c in comp_hand:
                suit_count[c.suit]+=1
            self.trump_suit=max(suit_count,key=suit_count.get)
        else:
            self.trump_suit=suit

    def attach_kitty(self):
        if self.bid_winner==1:
            # comp is bidder => comp sees kitty
            comp=self.players[1]
            comp.hand.extend(self.kitty)
            self.kitty=[]
        else:
            # user => reveal kitty
            self.kitty_revealed=True

    def discard_and_draw_comp(self):
        """
        Computer discards up to 4 from its hand (the user sees in the log how many).
        Then draws from deck. We'll do a simple strategy: keep trump + hearts A, discard everything else up to 4.
        """
        comp=self.players[1]
        if not comp.hand: return 0
        def keepTest(c):
            return (c.suit==self.trump_suit) or (c.suit=="Hearts" and c.rank=="A")
        toDiscard=[]
        for c in comp.hand:
            if not keepTest(c):
                toDiscard.append(c)
            if len(toDiscard)>=4:
                break
        discard_count=len(toDiscard)
        for c in toDiscard:
            comp.hand.remove(c)
        new_cards=self.deck.deal(discard_count)
        comp.hand.extend(new_cards)
        return discard_count

    def discard_and_draw_user(self, discardList):
        """
        The user selected up to 4 from their hand. We remove them, deal same number from deck.
        """
        user=self.players[0]
        removed=[]
        for d in discardList:
            for c in user.hand:
                if str(c)==d:
                    removed.append(c)
                    break
        for c in removed:
            user.hand.remove(c)
        new_cards=self.deck.deal(len(removed))
        user.hand.extend(new_cards)
        return len(removed)

    def finalize_kitty_selection(self, keepArr, discardArr):
        """
        Called when user is bidder and user is done with kitty. 
        They pick which kitty cards to keep, and also discards from their existing hand.
        Then the computer discards up to 4. Then we set leading_player = 0 (user).
        """
        if self.game_over:
            return {"discarded":[],"drawn":[]}
        user=self.players[0]
        # remove discardArr from user
        for d in discardArr:
            for c in user.hand:
                if str(c)==d:
                    user.hand.remove(c)
                    break
        # kitty keep
        kitty_keep=[]
        leftover=[]
        for c in self.kitty:
            if str(c) in keepArr:
                kitty_keep.append(c)
            else:
                leftover.append(c)
        user.hand.extend(kitty_keep)
        self.kitty=leftover
        self.kitty_revealed=False

        # if >5 => remove extras
        extras=[]
        while len(user.hand)>5:
            extras.append(user.hand.pop())
        new_cards=self.deck.deal(len(extras))
        user.hand.extend(new_cards)

        # now computer discards up to 4
        comp_discarded = self.discard_and_draw_comp()

        # user leads first trick
        self.leading_player=0
        self.kitty=[]
        return {"discarded":[str(x) for x in extras],"drawn":[str(c) for c in new_cards]}

    def finalize_kitty_selection_compLost(self, userDiscardList):
        """
        If comp is bidder, comp has already picked kitty behind the scenes, 
        now the user discards up to 4 from their existing hand, then we set leading_player=1 (computer).
        """
        if self.game_over:
            return {"discarded":[],"drawn":[]}
        user=self.players[0]
        removed=[]
        for d in userDiscardList:
            for c in user.hand:
                if str(c)==d:
                    removed.append(c)
                    break
        for c in removed:
            user.hand.remove(c)
        new_cards=self.deck.deal(len(removed))
        user.hand.extend(new_cards)

        # now first trick => comp leads
        self.leading_player=1
        return {"discarded":[str(x) for x in removed],"drawn":[str(c) for c in new_cards]}

    def record_high_card(self, card_obj, player_idx):
        rank_val=get_card_rank(str(card_obj), self.trump_suit)
        if self.highest_card_played is None:
            self.highest_card_played=str(card_obj)
            self.highest_card_owner=player_idx
        else:
            old_val=get_card_rank(self.highest_card_played,self.trump_suit)
            if rank_val>old_val:
                self.highest_card_played=str(card_obj)
                self.highest_card_owner=player_idx

    def play_trick_user(self, card_str):
        if self.game_over:
            return "Game is over. No more plays."
        user=self.players[0]
        if card_str not in [str(c) for c in user.hand]:
            return "Error: Card not in your hand."
        cobj=next(x for x in user.hand if str(x)==card_str)
        user.hand.remove(cobj)
        self.last_played_cards=[(user.name,str(cobj),card_to_image_url(str(cobj)))]
        self.record_high_card(cobj,0)

        comp=self.players[1]
        if self.leading_player==0:
            # user leads => comp follows
            follow=self.computer_follow(comp, cobj.suit)
            comp.hand.remove(follow)
            self.last_played_cards.append((comp.name,str(follow),card_to_image_url(str(follow))))
            self.record_high_card(follow,1)
            winner=self.evaluate_trick([(0,cobj),(1,follow)])
        else:
            # comp leads => already must pick from comp's hand => but we are in "user play" route, meaning we clicked user card???
            # Actually we should not let the user click if comp leads. 
            # We'll fix the logic in the front-end so you can't click if comp leads.
            return "It's the computer's turn to lead, you can't play first."
        self.players[winner].score+=5
        self.players[winner].tricks_won+=1
        self.leading_player=winner

        total_tricks=sum([p.tricks_won for p in self.players])
        if total_tricks>=5:
            self.auto_finalize()
        return f"Trick played. Winner: {self.players[winner].name}"

    def play_trick_comp_lead(self):
        """
        Called when the computer is leading. We pick a card from comp's hand, then the user responds.
        The front-end will then wait for the user to pick a card to respond. 
        So we might store the comp's lead in `last_played_cards` and wait for user to do "respondToCompLead"
        Alternatively, we can do it in multiple endpoints. 
        For simplicity, we'll store the comp's lead in last_played_cards, then the front-end can see it and let the user pick a response.
        """
        comp=self.players[1]
        lead=self.computer_lead(comp.hand)
        comp.hand.remove(lead)
        self.last_played_cards=[(comp.name,str(lead),card_to_image_url(str(lead)))]
        self.record_high_card(lead,1)
        return f"Computer leads {lead}"

    def respond_to_comp_lead(self, userCardName):
        """
        The user sees the comp's lead in self.last_played_cards[0], picks a response, we evaluate.
        """
        if self.game_over:
            return "Game is over, no more plays."
        user=self.players[0]
        if userCardName not in [str(c) for c in user.hand]:
            return "Error: Card not in your hand to respond."
        cobj=next(x for x in user.hand if str(x)==userCardName)
        user.hand.remove(cobj)
        self.last_played_cards.append((user.name,str(cobj),card_to_image_url(str(cobj))))
        self.record_high_card(cobj,0)
        # now evaluate the trick
        comp_lead_obj = self.last_played_cards[0][1]
        comp_lead_card = Card(*comp_lead_obj.split(" of "))
        user_card = cobj
        winner=self.evaluate_trick([(1,comp_lead_card),(0,user_card)])
        self.players[winner].score+=5
        self.players[winner].tricks_won+=1
        self.leading_player=winner
        total_tricks=sum([p.tricks_won for p in self.players])
        if total_tricks>=5:
            self.auto_finalize()
        return f"Trick completed. Winner: {self.players[winner].name}"

    def auto_finalize(self):
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score+=5
        if self.bid_winner is not None:
            bidderP=self.players[self.bid_winner]
            pointsEarned=bidderP.tricks_won*5
            if self.highest_card_owner==self.bid_winner:
                pointsEarned+=5
            if pointsEarned<self.bid:
                bidderP.score-=self.bid
        if self.players[0].score>=120 or self.players[1].score>=120:
            self.game_over=True
        else:
            self.rotate_dealer()
            self.reset_hand()
            self.deal_hands()

    def computer_lead(self,hand):
        hand.sort(key=lambda c:get_card_rank(str(c),self.trump_suit),reverse=True)
        return hand[0] if hand else None

    def computer_follow(self,comp,lead_suit):
        valid=[c for c in comp.hand if c.suit==lead_suit]
        if valid:
            valid.sort(key=lambda x:get_card_rank(str(x),self.trump_suit))
            return valid[0]
        else:
            comp.hand.sort(key=lambda x:get_card_rank(str(x),self.trump_suit))
            return comp.hand[0]

    def evaluate_trick(self,plays):
        lead_suit=plays[0][1].suit
        trumps=[(p,c) for(p,c) in plays if get_card_rank(str(c),self.trump_suit)>=100]
        if trumps:
            (win_pid, win_card)=max(trumps, key=lambda x:get_card_rank(str(x[1]),self.trump_suit))
        else:
            same=[(p,c) for(p,c) in plays if c.suit==lead_suit]
            (win_pid, win_card)=max(same,key=lambda x:get_card_rank(str(x[1]),self.trump_suit))
        return win_pid


###############################################################################
#                          FLASK ROUTES & GLOBALS                             #
###############################################################################
current_game=None

@app.route("/")
def index():
    global current_game
    if not current_game or current_game.game_over:
        current_game=Game()
        current_game.deal_hands()
    return main_html()

def main_html():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Forty-Fives - Corrected Bids & Discard Flow</title>
  <style>
    body { margin:0; padding:0; background:darkgreen; font-family:sans-serif; color:white; }
    #table { position:relative; width:100%; height:100vh; }
    /* Similar styling as before */
    /* ... */
  </style>
</head>
<body>
<!-- Single-page UI... 
     The rest is basically the same as before, no new/finalize hand buttons, 
     but the user can see who leads the first trick, etc. -->
</body>
</html>
"""

# You can replicate the same JavaScript that displays, logs, 
# leads the user to discard, etc. The crucial logic changes are in the Game class.

@app.route("/show_state", methods=["GET"])
def show_state():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}),400
    user=current_game.players[0]
    comp=current_game.players[1]
    if user.score>=120 or comp.score>=120:
        current_game.game_over=True
    your_cards=[{"name":str(c),"img":card_to_image_url(str(c))} for c in user.hand]
    kitty_list=[{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]

    bidderName=None
    if current_game.bid_winner is not None:
        bidderName=current_game.players[current_game.bid_winner].name

    state={
      "computer_count": len(comp.hand),
      "your_cards": your_cards,
      "kitty": kitty_list,
      "kitty_revealed": current_game.kitty_revealed,
      "card_back": card_back_url(),
      "deck_count": len(current_game.deck.cards),
      "last_trick": current_game.last_played_cards,
      "round_score_your": user.tricks_won*5,
      "round_score_comp": comp.tricks_won*5,
      "total_your": user.score,
      "total_comp": comp.score,
      "bidder": bidderName,
      "bid_submitted": (current_game.bid_winner is not None),
      "bidding_done": current_game.bidding_done,
      "trump_suit": current_game.trump_suit,
      "trump_set": (current_game.trump_suit is not None),
      "leading_player": current_game.leading_player,  # 0 => user leads, 1 => comp leads
      "show_kitty_confirm": (current_game.bid_winner==0 and current_game.kitty_revealed),
      "game_over": current_game.game_over
    }
    return jsonify(state)

@app.route("/user_bid", methods=["POST"])
def user_bid_route():
    global current_game
    data=request.get_json() or {}
    val=data.get("bid_val",0)
    msg=current_game.user_bid(val)
    return jsonify({"message":msg})

@app.route("/pick_trump", methods=["POST"])
def pick_trump():
    global current_game
    data=request.get_json() or {}
    suit=data.get("suit","Hearts")
    current_game.set_trump(suit)
    current_game.attach_kitty()
    return jsonify({"message":f"Trump suit set to {current_game.trump_suit}"})

@app.route("/finalize_kitty", methods=["POST"])
def finalize_kitty():
    global current_game
    data=request.get_json() or {}
    keepArr=data.get("keep",[])
    discardArr=data.get("discard",[])
    res=current_game.finalize_kitty_selection(keepArr, discardArr)
    return jsonify({"message":"Kitty selection done","details":res})

@app.route("/finalize_kitty_comp", methods=["POST"])
def finalize_kitty_comp():
    """
    If the computer won the bid, the user still gets one discard pass. 
    We'll call this route after user selects up to 4 from their hand. 
    Then we set leading_player=1 => comp leads the first trick.
    """
    global current_game
    data=request.get_json() or {}
    discList=data.get("discard",[])
    res=current_game.finalize_kitty_selection_compLost(discList)
    return jsonify({"message":"Your discard pass done.","details":res})

@app.route("/play_card_user", methods=["POST"])
def play_card_user():
    global current_game
    data=request.get_json() or {}
    cName=data.get("card_name")
    if not cName:
        return jsonify({"error":"No card."}),400
    out=current_game.play_trick_user(cName)
    return jsonify({"message":out})

@app.route("/comp_lead", methods=["POST"])
def comp_lead():
    """
    Called if the comp is leading. We pick a card from comp's hand, store it in last_played_cards,
    then the user can see it in show_state and respond with /respond_to_comp_lead.
    """
    global current_game
    if current_game.leading_player!=1:
        return jsonify({"error":"It's not the computer's lead."}),400
    msg=current_game.play_trick_comp_lead()
    return jsonify({"message":msg})

@app.route("/respond_to_comp_lead", methods=["POST"])
def respond_to_lead():
    global current_game
    data=request.get_json() or {}
    userCard=data.get("card_name")
    msg=current_game.respond_to_comp_lead(userCard)
    return jsonify({"message":msg})

@app.route("/user_draw", methods=["POST"])
def user_draw():
    global current_game
    data=request.get_json() or {}
    discList=data.get("discards",[])
    count=current_game.discard_and_draw_user(discList)
    return jsonify({"message":f"You discarded {count} card(s), and drew {count}."})

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
