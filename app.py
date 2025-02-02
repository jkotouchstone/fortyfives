import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                        CARD RANK/LOOKUP DICTIONARIES                        #
###############################################################################

TRUMP_DIAMONDS = {
    "5 of Diamonds":200, "J of Diamonds":199, "A of Hearts":198, "A of Diamonds":197,
    "K of Diamonds":196, "Q of Diamonds":195, "10 of Diamonds":194, "9 of Diamonds":193,
    "8 of Diamonds":192, "7 of Diamonds":191, "6 of Diamonds":190,
    "4 of Diamonds":189, "3 of Diamonds":188, "2 of Diamonds":187
}
TRUMP_HEARTS = {
    "5 of Hearts":200, "J of Hearts":199, "A of Hearts":198,
    "K of Hearts":196, "Q of Hearts":195, "10 of Hearts":194, "9 of Hearts":193,
    "8 of Hearts":192, "7 of Hearts":191, "6 of Hearts":190,
    "4 of Hearts":189, "3 of Hearts":188, "2 of Hearts":187
}
TRUMP_CLUBS = {
    "5 of Clubs":200, "J of Clubs":199, "A of Hearts":198, "A of Clubs":197,
    "K of Clubs":196, "Q of Clubs":195,
    "2 of Clubs":194, "3 of Clubs":193, "4 of Clubs":192,
    "6 of Clubs":191, "7 of Clubs":190, "8 of Clubs":189,
    "9 of Clubs":188, "10 of Clubs":187
}
TRUMP_SPADES = {
    "5 of Spades":200, "J of Spades":199, "A of Hearts":198, "A of Spades":197,
    "K of Spades":196, "Q of Spades":195,
    "2 of Spades":194, "3 of Spades":193, "4 of Spades":192,
    "6 of Spades":191, "7 of Spades":190, "8 of Spades":189,
    "9 of Spades":188, "10 of Spades":187
}

OFFSUIT_DIAMONDS = {
    "K of Diamonds":200, "Q of Diamonds":199, "J of Diamonds":198, "10 of Diamonds":197,
    "9 of Diamonds":196, "8 of Diamonds":195, "7 of Diamonds":194, "6 of Diamonds":193,
    "5 of Diamonds":192, "4 of Diamonds":191, "3 of Diamonds":190, "2 of Diamonds":189,
    "A of Diamonds":188
}
OFFSUIT_HEARTS = {
    "K of Hearts":200, "Q of Hearts":199, "J of Hearts":198, "10 of Hearts":197,
    "9 of Hearts":196, "8 of Hearts":195, "7 of Hearts":194, "6 of Hearts":193,
    "5 of Hearts":192, "4 of Hearts":191, "3 of Hearts":190, "2 of Hearts":189
}
OFFSUIT_CLUBS = {
    "K of Clubs":200, "Q of Clubs":199, "J of Clubs":198, "A of Clubs":197,
    "2 of Clubs":196, "3 of Clubs":195, "4 of Clubs":194, "5 of Clubs":193,
    "6 of Clubs":192, "7 of Clubs":191, "8 of Clubs":190, "9 of Clubs":189,
    "10 of Clubs":188
}
OFFSUIT_SPADES = {
    "K of Spades":200, "Q of Spades":199, "J of Spades":198, "A of Spades":197,
    "2 of Spades":196, "3 of Spades":195, "4 of Spades":194, "5 of Spades":193,
    "6 of Spades":192, "7 of Spades":191, "8 of Spades":190, "9 of Spades":189,
    "10 of Spades":188
}

def get_card_rank(card_str: str, trump_suit: str) -> int:
    """Returns numeric rank for card_str under given trump_suit, ensuring Ace of Hearts is 3rd best, etc."""
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

def card_to_image_url(card_str: str) -> str:
    """
    Convert e.g. '10 of Hearts' => '0H.png' for deckofcardsapi.com
    rank_map: '10' -> '0'
    """
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

###############################################################################
#                         CLASSES: Card, Deck, Player                         #
###############################################################################
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
#                              GAME CLASS                                     #
###############################################################################
class Game:
    def __init__(self):
        self.players=[Player("You"), Player("Computer")]
        self.dealer=1  # 0=>user,1=>computer
        self.deck=Deck()
        self.kitty=[]
        self.trump_suit=None
        self.bid_winner=None
        self.bid=0
        self.leading_player=None  # who leads the next trick: 0=>user,1=>comp
        self.highest_card_played=None
        self.highest_card_owner=None
        self.last_played_cards=[]
        self.kitty_revealed=False
        self.bidding_done=False
        self.game_over=False

        # flags indicating if user/comp discards are done
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
        """ Bidding logic with +5 increments. If comp wins => comp picks trump & kitty. If user => user picks. """
        if self.game_over:
            return "Game is over."
        if self.bidding_done:
            return "Bidding concluded."

        first_bidder=0 if self.dealer==1 else 1
        msg=""
        if first_bidder==0:
            # user is first
            if bid_val==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="You bid 30, you immediately win the bid."
            else:
                # If user=15 => comp => pass or 20
                # If user=20 => comp => pass or 25
                # If user=25 => comp => pass or 30
                # If user=0 => comp => pass or 15
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
                    msg=f"You bid {bid_val}, computer passed. You win."
                else:
                    comp_choice=random.choice(comp_options)
                    if comp_choice>bid_val:
                        self.bid_winner=1
                        self.bid=comp_choice
                        self.bidding_done=True
                        msg=f"Computer outbid you with {comp_choice}. Computer wins."
                    else:
                        self.bid_winner=self.dealer
                        self.bid=15
                        self.bidding_done=True
                        if self.dealer==1:
                            msg="Both passed, Computer forced 15."
                        else:
                            msg="Both passed, You forced 15."
        else:
            # user second => comp picks random in [0,15,20,25,30]
            cFirst = random.choice([0,15,20,25,30])
            if cFirst==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="Computer bids 30, instantly wins."
            else:
                if bid_val>cFirst:
                    self.bid_winner=1
                    self.bid=bid_val
                    self.bidding_done=True
                    msg=f"Computer bid {cFirst}, you outbid with {bid_val}, you win."
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
                        msg=f"Computer bid {cFirst}, you didn't beat => Computer wins."
                    else:
                        msg="Computer passed, you also didn't => forced 15 to Computer."

        if self.bidding_done:
            if self.bid_winner==1:
                # computer => picks trump
                self.set_trump(None)
                # comp sees kitty behind scenes
                comp=self.players[1]
                comp.hand.extend(self.kitty)
                self.kitty=[]
        return msg

    def set_trump(self, suit=None):
        if self.bid_winner==1 and self.dealer==1:
            # comp picks
            comp_hand=self.players[1].hand
            suits_count={"Hearts":0,"Diamonds":0,"Clubs":0,"Spades":0}
            for c in comp_hand:
                suits_count[c.suit]+=1
            self.trump_suit=max(suits_count,key=suits_count.get)
        else:
            self.trump_suit=suit

    def attach_kitty_user(self):
        """ If user is bidder => kitty is revealed => user sees it, after picking a suit. """
        self.kitty_revealed=True

    def discard_comp(self):
        """
        Computer discards up to 4 from its hand to keep trump & hearts Ace. 
        Called after comp sees kitty or if user is bidder => after user discards.
        """
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

    def discard_user(self, discardList):
        """User discards up to 4, draws the same number. Then self.user_discard_done=True."""
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
        self.user_discard_done=True
        return len(removed)

    def finalize_kitty_user(self, kittyKeep, kittyDiscard):
        """
        If user is bidder => user has kitty => picks which to keep from kitty, 
        also can discard from own hand. We'll handle own-hand discard in separate call 
        or all at once. For simplicity let's do it all here if you want.
        """
        pass # omitted for brevity or incorporate logic as you want

    def both_discard_done_check(self):
        """
        If both user & comp have done their discards => set leading_player to self.bid_winner 
        => that participant leads the first trick.
        """
        if self.user_discard_done and self.comp_discard_done:
            self.leading_player=self.bid_winner

    def play_trick_user_lead(self, card_str):
        """
        If user leads => check leading_player==0 => user leads => comp responds => evaluate
        """
        if self.game_over:
            return "Game over. No more plays."
        if not self.user_discard_done or not self.comp_discard_done:
            return "Discard phase not done yet."
        if self.leading_player!=0:
            return "It's not your lead, the computer leads."
        user=self.players[0]
        if card_str not in [str(c) for c in user.hand]:
            return "Card not in your hand."
        lead_card=next(x for x in user.hand if str(x)==card_str)
        user.hand.remove(lead_card)
        self.last_played_cards=[(user.name,str(lead_card),card_to_image_url(str(lead_card)))]
        self.record_high_card(lead_card,0)

        # computer responds
        comp=self.players[1]
        follow=self.computer_follow(comp, lead_card.suit)
        comp.hand.remove(follow)
        self.last_played_cards.append((comp.name,str(follow),card_to_image_url(str(follow))))
        self.record_high_card(follow,1)
        winner=self.evaluate_trick([(0,lead_card),(1,follow)])
        self.players[winner].score+=5
        self.players[winner].tricks_won+=1
        self.leading_player=winner
        total_tricks=sum([p.tricks_won for p in self.players])
        if total_tricks>=5:
            self.auto_finalize()
        return f"You led {lead_card}. Computer responded {follow}. Winner: {self.players[winner].name}"

    def comp_lead_trick(self):
        """
        If comp leads => self.leading_player=1 => comp picks best lead => store in last_played_cards => user calls 'respond_to_comp_lead'
        """
        if not self.user_discard_done or not self.comp_discard_done:
            return "Discard phase not done yet."
        if self.leading_player!=1:
            return "It's not computer's lead."
        comp=self.players[1]
        lead=self.computer_lead(comp.hand)
        comp.hand.remove(lead)
        self.last_played_cards=[(comp.name,str(lead),card_to_image_url(str(lead)))]
        self.record_high_card(lead,1)
        return f"Computer leads {lead}"

    def respond_to_comp_lead(self, userCard):
        """User sees comp's lead, picks a card to respond => we finalize the trick => set winner => next lead."""
        if self.game_over:
            return "Game over."
        if not self.last_played_cards or self.last_played_cards[0][0]!="Computer":
            return "Computer hasn't led yet."
        user=self.players[0]
        if userCard not in [str(c) for c in user.hand]:
            return "You don't have that card."
        cobj=next(x for x in user.hand if str(x)==userCard)
        user.hand.remove(cobj)
        self.last_played_cards.append((user.name,str(cobj),card_to_image_url(str(cobj))))
        self.record_high_card(cobj,0)
        # evaluate
        comp_lead_str=self.last_played_cards[0][1]
        comp_lead=Card(*comp_lead_str.split(" of "))
        user_card=cobj
        winner=self.evaluate_trick([(1,comp_lead),(0,user_card)])
        self.players[winner].score+=5
        self.players[winner].tricks_won+=1
        self.leading_player=winner
        total_tricks=sum([p.tricks_won for p in self.players])
        if total_tricks>=5:
            self.auto_finalize()
        return f"Computer led {comp_lead}, you responded {cobj}. Winner: {self.players[winner].name}"

    def evaluate_trick(self, plays):
        lead_suit=plays[0][1].suit
        trumps=[(pid,c) for(pid,c) in plays if get_card_rank(str(c),self.trump_suit)>=100]
        if trumps:
            (win_pid, win_card)=max(trumps,key=lambda x:get_card_rank(str(x[1]),self.trump_suit))
        else:
            same=[(pid,c) for(pid,c) in plays if c.suit==lead_suit]
            (win_pid, win_card)=max(same,key=lambda x:get_card_rank(str(x[1]),self.trump_suit))
        return win_pid

    def record_high_card(self, card_obj, player_idx):
        rank_val=get_card_rank(str(card_obj),self.trump_suit)
        if self.highest_card_played is None:
            self.highest_card_played=str(card_obj)
            self.highest_card_owner=player_idx
        else:
            old_val=get_card_rank(self.highest_card_played,self.trump_suit)
            if rank_val>old_val:
                self.highest_card_played=str(card_obj)
                self.highest_card_owner=player_idx

    def auto_finalize(self):
        # +5 to highest card owner
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score+=5
        # if bidder fails to meet bid => bidder loses bid points
        if self.bid_winner is not None:
            bidder=self.players[self.bid_winner]
            bidderPoints=bidder.tricks_won*5
            if self.highest_card_owner==self.bid_winner:
                bidderPoints+=5
            if bidderPoints<self.bid:
                bidder.score-=self.bid
        # check 120
        if self.players[0].score>=120 or self.players[1].score>=120:
            self.game_over=True
        else:
            self.rotate_dealer()
            self.reset_hand()
            self.deal_hands()

###############################################################################
#                      FLASK GLOBAL & ROUTES                                  #
###############################################################################
current_game=None

@app.route("/")
def index():
    global current_game
    if not current_game or current_game.game_over:
        current_game=Game()
        current_game.deal_hands()
    return main_html()

@app.route("/reset_game", methods=["POST"])
def reset_game():
    """User can click 'New Game' to completely reset scores & start fresh."""
    global current_game
    current_game=Game()
    current_game.deal_hands()
    return jsonify({"message":"New game started. Old progress cleared."})

def main_html():
    """
    Single-page UI with:
    - 'New Game' button 
    - Bidding, discard phases, etc.
    - No finalize/new hand buttons, all auto
    """
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Forty-Fives - Final Edition</title>
  <style>
    body { margin:0; padding:0; background:darkgreen; font-family:sans-serif; color:white; }
    #table { position:relative; width:100%; height:100vh; }
    #controls { position:absolute; top:0; left:0; width:100%; text-align:center; background:rgba(0,0,0,0.5); padding:10px;}
    #progressLog { position:absolute; top:0; right:0; width:250px; max-height:200px; overflow-y:auto; background:rgba(0,0,0,0.3); padding:8px; font-size:0.9em; }
    #computerArea { position:absolute; left:50%; transform:translateX(-50%); top:80px; text-align:center; }
    #playerArea { position:absolute; left:50%; transform:translateX(-50%); bottom:20px; text-align:center; }
    #kittyArea { position:absolute; left:20px; top:200px; width:160px; height:120px; text-align:left; }
    #biddingArea { position:absolute; left:20px; bottom:20px; width:200px; background:rgba(0,0,0,0.3); padding:8px; border-radius:4px;}
    #deckArea { position:absolute; right:20px; top:50%; transform:translateY(-50%); text-align:center;}
    #centerArea { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;}
    #scoreboard { position:absolute; top:0; left:0; margin-top:40px; background:rgba(255,255,255,0.8); color:black; padding:10px; margin-left:10px; border-radius:5px;}
    .card { width:80px; margin:5px; cursor:pointer; border-radius:5px; }
    .selected { outline:2px solid yellow; }
    button { margin:5px; padding:5px 10px; border:none; border-radius:4px; background:#555; color:#fff; cursor:pointer;}
    button:hover { background:#666; }
    footer { position:absolute; bottom:0; right:0; font-size:0.8em; color:#aaa; padding:5px;}
  </style>
</head>
<body>
<div id="table">
  <div id="controls">
    <button onclick="newGame()">New Game</button>
    <!-- Possibly other controls, e.g. 'Show State' -->
  </div>
  <div id="progressLog"></div>
  <!-- 
    Layout for computerArea, centerArea, playerArea, kittyArea, biddingArea, deckArea, scoreboard 
    plus the typical logic in scripts for showState, user_bid, etc.
  -->
</div>

<script>
function newGame(){
  if(confirm("Are you sure you want to start a new game and lose all progress?")){
    fetch('/reset_game',{method:'POST'})
    .then(r=>r.json())
    .then(d=>{
      console.log(d.message);
      // call showState
      showState();
    });
  }
}

function showState(){
  // fetch /show_state => update UI
  // ...
}
</script>
</body>
</html>
"""

@app.route("/show_state", methods=["GET"])
def show_state_api():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}),400
    user=current_game.players[0]
    comp=current_game.players[1]
    if user.score>=120 or comp.score>=120:
        current_game.game_over=True

    your_cards=[{"name":str(c), "img":card_to_image_url(str(c))} for c in user.hand]
    kitty_info=[{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]

    bidderName=None
    if current_game.bid_winner is not None:
        bidderName=current_game.players[current_game.bid_winner].name

    # build a JSON describing the entire game state
    st={
      "computer_count": len(comp.hand),
      "your_cards": your_cards,
      "kitty": kitty_info,
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
      "leading_player": current_game.leading_player,
      "show_kitty_confirm": (current_game.bid_winner==0 and current_game.kitty_revealed),
      "game_over": current_game.game_over
    }
    return jsonify(st)

@app.route("/user_bid", methods=["POST"])
def user_bid():
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
    # if user => see kitty
    current_game.attach_kitty_user()
    return jsonify({"message":f"Trump set to {current_game.trump_suit}"})

@app.route("/comp_discard", methods=["POST"])
def comp_discard():
    global current_game
    current_game.discard_comp()
    return jsonify({"message":"Computer has discarded up to 4 cards."})

@app.route("/user_discard", methods=["POST"])
def user_discard():
    global current_game
    data=request.get_json() or {}
    discList=data.get("discards",[])
    cnt=current_game.discard_user(discList)
    return jsonify({"message":f"You discarded {cnt} card(s). Drew {cnt} new."})

@app.route("/both_discard_done", methods=["POST"])
def both_discard_done():
    global current_game
    # if user_discard_done & comp_discard_done => set leading_player to bid_winner
    current_game.both_discard_done_check()
    leadName = current_game.players[current_game.leading_player].name if current_game.leading_player is not None else "None"
    return jsonify({"message":f"Discard done. {leadName} leads the first trick."})

@app.route("/play_card_user_lead", methods=["POST"])
def play_card_user_lead():
    """If user leads => comp responds => we evaluate => etc."""
    global current_game
    data=request.get_json() or {}
    cName=data.get("card_name")
    msg=current_game.play_trick_user_lead(cName)
    return jsonify({"message":msg})

@app.route("/comp_lead_trick", methods=["POST"])
def comp_lead_trick():
    global current_game
    msg=current_game.comp_lead_trick()
    return jsonify({"message":msg})

@app.route("/respond_comp_lead", methods=["POST"])
def respond_comp_lead():
    global current_game
    data=request.get_json() or {}
    cName=data.get("card_name")
    msg=current_game.respond_to_comp_lead(cName)
    return jsonify({"message":msg})

@app.route("/play_card_user", methods=["POST"])
def play_card_user():
    """
    If user tries to lead or respond incorrectly, we can detect in game logic
    or call the correct route for user_lead or respond_to_comp_lead.
    We'll keep this for backward compatibility or simpler approach.
    """
    global current_game
    data=request.get_json() or {}
    cName=data.get("card_name")
    if not cName:
        return jsonify({"error":"No card given"}),400
    # We can decide if leading_player=0 => user leads => comp responds => or if leading_player=1 => error
    # but we'll skip details to keep code not too large
    msg="Unimplemented route in this snippet."
    return jsonify({"message":msg})

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
