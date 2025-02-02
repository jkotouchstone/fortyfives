import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                           CARD RANK LOOKUPS                                 #
###############################################################################
# Each dictionary ensures: 5 => 200, J => 199, A of Hearts => 198, etc.
# So that Ace of Hearts is the 3rd best card behind 5 and J in the appropriate suit.

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
    """Look up numeric rank for card_str under the given trump_suit."""
    if not trump_suit:
        return 0
    if trump_suit=="Diamonds":
        if card_str in TRUMP_DIAMONDS:
            return TRUMP_DIAMONDS[card_str]
        # else fallback hearts/clubs/spades off-suit dict
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

###############################################################################
#                          CARD IMAGE LOGIC                                   #
###############################################################################
def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    """
    Convert e.g. '10 of Hearts' => '0H.png' for deckofcardsapi.
    """
    parts = card_str.split(" of ")
    if len(parts)!=2:
        return card_back_url()
    rank, suit=parts
    rank_map = {
        "2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9",
        "10":"0","J":"J","Q":"Q","K":"K","A":"A"
    }
    if rank not in rank_map:
        return card_back_url()
    rank_code = rank_map[rank]  # "0" if rank=="10"
    suit_code = suit[0].upper() # 'H','D','C','S'
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

###############################################################################
#                      CLASSES: Card, Deck, Player, Game                      #
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
#                               MAIN Game Class                               #
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
        self.leading_player=0
        self.highest_card_played=None
        self.highest_card_owner=None
        self.last_played_cards=[]
        self.kitty_revealed=False
        self.bidding_done=False
        self.game_over=False

        # For improved discard logic: after the computer wins the bid, 
        # we track how many cards it discards so we can show it to the user.

        self.computer_discard_count=0  
        self.user_discard_count=0  

    def rotate_dealer(self):
        self.dealer=1-self.dealer

    def reset_hand(self):
        self.deck=Deck()
        self.kitty=[]
        self.trump_suit=None
        self.bid_winner=None
        self.bid=0
        self.leading_player=0
        self.highest_card_played=None
        self.highest_card_owner=None
        self.last_played_cards=[]
        self.kitty_revealed=False
        self.bidding_done=False
        self.computer_discard_count=0
        self.user_discard_count=0
        for p in self.players:
            p.hand.clear()
            p.tricks_won=0

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand.clear()
        self.kitty=[]
        self.computer_discard_count=0
        self.user_discard_count=0

        first_bidder=0 if self.dealer==1 else 1
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self,bid_val):
        if self.bidding_done or self.game_over:
            return "No bidding possible now."
        first_bidder=0 if self.dealer==1 else 1
        msg=""

        # +5 increments
        if first_bidder==0:
            # user is first
            if bid_val==30:
                self.bid_winner=0
                self.bid=30
                self.bidding_done=True
                msg="You bid 30, you immediately win the bid."
            else:
                comp_options=[]
                # user=15 => comp can do [0,20]
                # user=20 => comp can do [0,25]
                # user=25 => comp can do [0,30]
                # user=0 => comp can do [0,15]
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
            # user second => comp first => random among [0,15,20,25,30]
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
                    msg=f"Computer bid {comp_first}, you matched => you win."
                else:
                    self.bid_winner=0
                    self.bid= comp_first if comp_first>0 else 15
                    self.bidding_done=True
                    if comp_first>0:
                        msg=f"Computer bid {comp_first}, you didn't beat it => Computer wins."
                    else:
                        msg="Computer passed, you also didn't bid => forced 15 to Computer."

        # if comp is bidder => pick trump + kitty, then autoDiscardComputer
        if self.bidding_done and self.bid_winner==1:
            self.set_trump(None)
            self.attach_kitty()
            # after picking up kitty, computer discards up to 4
            self.computerDiscardAndDraw()

        return msg

    def set_trump(self, suit=None):
        if self.bid_winner==1 and self.dealer==1:
            comp_hand=self.players[1].hand
            sc={"Hearts":0,"Diamonds":0,"Clubs":0,"Spades":0}
            for c in comp_hand:
                sc[c.suit]+=1
            self.trump_suit=max(sc,key=sc.get)
        else:
            self.trump_suit=suit

    def attach_kitty(self):
        if self.bid_winner==1:
            # computer sees kitty => hidden from user
            comp=self.players[1]
            comp.hand.extend(self.kitty)
            self.kitty=[]
        else:
            # user sees kitty
            self.kitty_revealed=True

    def computerDiscardAndDraw(self):
        """
        If computer is bidder, it picks up kitty, discards up to 4, draws from deck.
        We log how many it discards for the user to see.
        """
        comp = self.players[1]
        # example strategy: keep trump & heartsAce, discard everything else up to 4
        toDiscard=[]
        def keepTest(c):
            return (c.suit==self.trump_suit) or (c.suit=="Hearts" and c.rank=="A")
        for c in comp.hand:
            if not keepTest(c):
                toDiscard.append(c)
            if len(toDiscard)>=4:
                break
        for c in toDiscard:
            comp.hand.remove(c)
        discCount=len(toDiscard)
        new_cards=self.deck.deal(discCount)
        comp.hand.extend(new_cards)
        self.computer_discard_count=discCount

    def finalize_kitty_selection(self, keepArr, discardArr):
        """
        If user is bidder => user picks kitty.
        Then the user can also discard from their old hand. 
        We'll also discard up to 4 from computer if user is bidder 
        so the user can see how many the computer discards, 
        then proceed to trick phase.
        """
        user=self.players[0]
        # remove discardArr from user
        for d in discardArr:
            for c in user.hand:
                if str(c)==d:
                    user.hand.remove(c)
                    break

        # keep from kitty
        kitty_keep=[]
        kitty_left=[]
        for c in self.kitty:
            if str(c) in keepArr:
                kitty_keep.append(c)
            else:
                kitty_left.append(c)
        user.hand.extend(kitty_keep)
        self.kitty=kitty_left
        self.kitty_revealed=False

        # if more than 5 in user hand => discard extras
        discards=[]
        while len(user.hand)>5:
            discards.append(str(user.hand.pop()))
        new_cards=self.deck.deal(len(discards))
        user.hand.extend(new_cards)
        userDiscardCount=len(discardArr)+len(discards)
        self.user_discard_count=userDiscardCount

        # if user is bidder => now let computer discard up to 4
        if self.bid_winner==0:
            self.computerDiscardAndDraw()

        self.kitty=[]
        return {"discarded":discards,"drawn":[str(c) for c in new_cards]}

    def record_high_card(self, card_obj, player_idx):
        rank_val=get_card_rank(str(card_obj), self.trump_suit)
        if self.highest_card_played is None:
            self.highest_card_played=str(card_obj)
            self.highest_card_owner=player_idx
        else:
            old_val=get_card_rank(self.highest_card_played, self.trump_suit)
            if rank_val>old_val:
                self.highest_card_played=str(card_obj)
                self.highest_card_owner=player_idx

    def play_trick_user(self, card_str):
        if self.game_over:
            return "Game is over, no more play."
        user=self.players[0]
        if card_str not in [str(c) for c in user.hand]:
            return "Error: Card not in your hand."
        cobj=next(x for x in user.hand if str(x)==card_str)
        user.hand.remove(cobj)
        self.last_played_cards=[(user.name,str(cobj),card_to_image_url(str(cobj)))]
        self.record_high_card(cobj,0)
        comp=self.players[1]
        if self.leading_player==0:
            # comp follows
            follow=self.computer_follow(comp, cobj.suit)
            comp.hand.remove(follow)
            self.last_played_cards.append((comp.name,str(follow),card_to_image_url(str(follow))))
            self.record_high_card(follow,1)
            winner=self.evaluate_trick([(0,cobj),(1,follow)])
        else:
            # comp leads
            lead=self.computer_lead(comp.hand)
            comp.hand.remove(lead)
            self.last_played_cards=[
              (comp.name,str(lead),card_to_image_url(str(lead))),
              (user.name,str(cobj),card_to_image_url(str(cobj)))
            ]
            self.record_high_card(lead,1)
            winner=self.evaluate_trick([(1,lead),(0,cobj)])
        self.players[winner].score+=5
        self.players[winner].tricks_won+=1
        self.leading_player=winner

        # check if 5 total tricks => finalize
        total_tricks=sum([p.tricks_won for p in self.players])
        if total_tricks>=5:
            self.auto_finalize()
        return f"Trick played. Winner: {self.players[winner].name}"

    def auto_finalize(self):
        # highest card => +5
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score+=5
        # if bidder missed the bid => subtract
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
            # new hand
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
#                               FLASK ROUTES                                  #
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
    """Single-page UI with no new/finalize buttons; auto-hand, auto-finalize."""
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Forty-Fives - Corrections & QC</title>
  <style>
    body { margin:0; padding:0; background:darkgreen; font-family:sans-serif; color:white; }
    #table { position:relative; width:100%; height:100vh; }
    #progressLog {
      position:absolute; top:0; right:0; width:270px; max-height:200px; overflow-y:auto;
      background:rgba(0,0,0,0.3); padding:8px; font-size:0.9em;
    }
    #computerArea {
      position:absolute; left:50%; transform:translateX(-50%);
      top:80px; text-align:center;
    }
    #playerArea {
      position:absolute; left:50%; transform:translateX(-50%);
      bottom:20px; text-align:center;
    }
    #kittyArea {
      position:absolute; left:20px; top:200px;
      width:160px; height:120px; text-align:left;
    }
    #kittyStack { position:relative; width:80px; height:120px; margin-left:20px; }
    #kittyStack img { position:absolute; top:0; left:0; transition: all 0.2s ease; }
    #biddingArea {
      position:absolute; left:20px; bottom:20px;
      width:200px; background:rgba(0,0,0,0.3); padding:8px; border-radius:4px;
    }
    #deckArea {
      position:absolute; right:20px; top:50%; transform:translateY(-50%); text-align:center;
    }
    .deckClick { border:2px solid yellow; }
    #centerArea {
      position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
      text-align:center;
    }
    #trumpIcon {
      margin-top:5px; font-size:2em; color:yellow;
      height:40px; width:40px; display:inline-block;
    }
    #scoreboard {
      position:absolute; top:0; left:0; margin-top:40px;
      background:rgba(255,255,255,0.8); color:black; padding:10px; margin-left:10px; border-radius:5px;
    }
    .card { width:80px; margin:5px; cursor:pointer; border-radius:5px; }
    .selected { outline:2px solid yellow; }
    button { margin:5px; padding:5px 10px; border:none; border-radius:4px; background:#555; color:white; cursor:pointer; }
    button:hover { background:#666; }
    footer {
      position:absolute; bottom:0; right:0; color:#aaa; font-size:0.8em; padding:5px;
    }
  </style>
</head>
<body>
<div id="table">
  <div id="progressLog"></div>

  <div id="computerArea">
    <h3>Computer's Hand</h3>
    <div id="computerHand"></div>
  </div>

  <div id="centerArea">
    <h3>Current Trick</h3>
    <div id="trickArea"></div>
    <div id="trumpIcon"></div>
  </div>

  <div id="playerArea">
    <h3>Your Hand</h3>
    <div id="playerHand"></div>
  </div>

  <div id="kittyArea">
    <h3>Kitty</h3>
    <div id="kittyStack"></div>
    <button id="confirmKittyBtn" style="display:none" onclick="confirmKitty()">Confirm Kitty</button>
  </div>

  <div id="biddingArea">
    <h3>Bidding / Trump</h3>
    <div id="bidButtons"></div>
    <div id="trumpButtons" style="display:none">
      <p>Select Trump:</p>
      <button onclick="selectTrump('Hearts')">Hearts</button>
      <button onclick="selectTrump('Diamonds')">Diamonds</button>
      <button onclick="selectTrump('Clubs')">Clubs</button>
      <button onclick="selectTrump('Spades')">Spades</button>
    </div>
  </div>

  <div id="deckArea">
    <h3>Deck</h3>
    <img id="deckImg" class="card" src="" onclick="clickDeck()" />
    <div id="deckCount"></div>
  </div>

  <div id="scoreboard">
    <h3>Score Notebook</h3>
    <div id="scoreInfo"></div>
  </div>

  <footer>© O'Donohue Software</footer>
</div>

<script>
let gameState={};
let selectedKitty=[];
let discardSelection=[];

function log(msg){
  const logDiv=document.getElementById('progressLog');
  const p=document.createElement('p');
  p.textContent=msg;
  logDiv.appendChild(p);
  logDiv.scrollTop=logDiv.scrollHeight;
}

function showState(){
  fetch('/show_state')
   .then(r=>r.json())
   .then(d=>{
     if(d.error){
       log(d.error);
       return;
     }
     gameState=d;
     updateComputerHand(d.computer_count, d.card_back);
     updatePlayerHand(d.your_cards);
     updateKitty(d);
     updateDeck(d);
     updateTrick(d.last_trick);
     updateScores(d);
     updateBiddingUI(d);
     updateTrumpIcon(d.trump_suit);

     if(d.game_over){
       log("Game Over! " + (d.total_your>=120 ? "You" : "Computer") + " wins the game.");
     }
   });
}

function updateComputerHand(count, backUrl){
  let ch=document.getElementById('computerHand');
  ch.innerHTML="";
  for(let i=0;i<count;i++){
    let img=document.createElement('img');
    img.src=backUrl;
    img.className="card";
    ch.appendChild(img);
  }
}

function updatePlayerHand(cards){
  let ph=document.getElementById('playerHand');
  ph.innerHTML="";
  discardSelection=discardSelection.filter(x=> cards.map(c=>c.name).includes(x));
  cards.forEach(c=>{
    let img=document.createElement('img');
    img.src=c.img; // fixed rank mapping for deckofcardsapi
    img.className="card";
    img.onclick=()=>{
      if(gameState.game_over){
        log("Game is over, no more plays.");
        return;
      }
      if(gameState.trump_set && gameState.bidding_done){
        playCard(c.name);
      } else {
        toggleDiscard(c.name);
      }
    };
    if(discardSelection.includes(c.name)){
      img.classList.add('selected');
    }
    ph.appendChild(img);
  });
}

function toggleDiscard(cardName){
  if(discardSelection.includes(cardName)){
    discardSelection=discardSelection.filter(x=> x!==cardName);
  } else {
    if(discardSelection.length<4){
      discardSelection.push(cardName);
    } else {
      log("Max discard is 4.");
    }
  }
  showState();
}

function updateKitty(d){
  let ks=document.getElementById('kittyStack');
  ks.innerHTML="";
  selectedKitty=selectedKitty.filter(x=> d.kitty.map(k=>k.name).includes(x));

  document.getElementById('confirmKittyBtn').style.display = d.show_kitty_confirm ? "inline-block" : "none";
  if(d.kitty_revealed){
    d.kitty.forEach((kcard,i)=>{
      let img=document.createElement('img');
      img.src=kcard.img;
      img.className="card";
      img.style.zIndex=i;
      img.style.left=(i*20)+"px";
      img.onclick=()=>{
        if(selectedKitty.includes(kcard.name)){
          selectedKitty=selectedKitty.filter(x=>x!==kcard.name);
        } else {
          if(selectedKitty.length<3){
            selectedKitty.push(kcard.name);
          } else {
            log("Kitty selection typically up to 3. We'll allow more if you want.");
          }
        }
        updateKitty(d);
      };
      if(selectedKitty.includes(kcard.name)){
        img.classList.add('selected');
      }
      ks.appendChild(img);
    });
  } else {
    d.kitty.forEach((_,i)=>{
      let img=document.createElement('img');
      img.src=d.card_back;
      img.className="card";
      img.style.zIndex=i;
      img.style.left=(i*20)+"px";
      ks.appendChild(img);
    });
  }
}

function updateDeck(d){
  let dk=document.getElementById('deckImg');
  dk.src=d.card_back;
  if(!d.trump_set || !d.bidding_done){
    dk.classList.add('deckClick');
  } else {
    dk.classList.remove('deckClick');
  }
  document.getElementById('deckCount').textContent="Remaining: " + d.deck_count;
}

function updateTrick(trickData){
  let t=document.getElementById('trickArea');
  t.innerHTML="";
  if(trickData && trickData.length>0){
    trickData.forEach(item=>{
      let [pname,cstr,cimg]=item;
      let img=document.createElement('img');
      img.src=cimg;
      img.className="card";
      t.appendChild(img);
    });
  }
}

function updateScores(d){
  let sc=document.getElementById('scoreInfo');
  sc.innerHTML="Trick Pts - You:"+d.round_score_your+", Comp:"+d.round_score_comp
    + "<br>Total: You "+d.total_your+", Comp "+d.total_comp
    + (d.game_over ? "<br>GAME OVER!":"");
}

function updateBiddingUI(d){
  let bidDiv=document.getElementById('bidButtons');
  bidDiv.innerHTML="";
  let tDiv=document.getElementById('trumpButtons');
  tDiv.style.display= d.trump_set ? "none" : "none";

  if(d.game_over){
    return;
  }
  if(!d.bidding_done){
    let bids=[0,15,20,25,30];
    bids.forEach(bv=>{
      let label=(bv===0)?"Pass":"Bid "+bv;
      let btn=document.createElement('button');
      btn.textContent=label;
      btn.onclick=()=>{
        if(d.game_over){
          log("Game over, no bidding.");
          return;
        }
        fetch('/user_bid',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({bid_val: bv})
        })
         .then(r=>r.json())
         .then(resp=>{
           log(resp.message);
           showState();
         });
      };
      bidDiv.appendChild(btn);
    });
  } else {
    // if user is bidder => show trump
    if(d.bidder=="You" && !d.trump_set){
      tDiv.style.display="block";
    }
  }
}

function updateTrumpIcon(suit){
  let ti=document.getElementById('trumpIcon');
  ti.textContent="";
  if(!suit) return;
  let icon="";
  if(suit=="Hearts") icon="♥";
  else if(suit=="Diamonds") icon="♦";
  else if(suit=="Clubs") icon="♣";
  else if(suit=="Spades") icon="♠";
  ti.textContent=icon;
}

function confirmKitty(){
  fetch('/finalize_kitty',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ keep:selectedKitty, discard:[] })
  })
   .then(r=>r.json())
   .then(resp=>{
     log(resp.message);
     selectedKitty=[];
     showState();
   });
}

function clickDeck(){
  if(gameState.game_over){
    log("Game is over, no further draws.");
    return;
  }
  if(!gameState.trump_set || !gameState.bidding_done){
    if(discardSelection.length>0){
      fetch('/user_draw',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ discards: discardSelection })
      })
       .then(r=>r.json())
       .then(dd=>{
         log(dd.message);
         discardSelection=[];
         showState();
       });
    } else {
      log("No cards selected to discard.");
    }
  } else {
    log("Deck is not clickable during trick play.");
  }
}

function playCard(cardName){
  if(gameState.game_over){
    log("Game is over, no more plays.");
    return;
  }
  fetch('/play_card_user',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({card_name: cardName})
  })
   .then(r=>r.json())
   .then(resp=>{
     log(resp.message);
     showState();
   });
}

window.onload=()=>showState();
</script>
"""

@app.route("/show_state", methods=["GET"])
def show_state_api():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}),400

    user = current_game.players[0]
    comp = current_game.players[1]

    # If user or comp =>120 => game_over
    if user.score>=120 or comp.score>=120:
        current_game.game_over=True

    your_cards = [{"name":str(c),"img":card_to_image_url(str(c))} for c in user.hand]
    kitty_data = [{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]
    bidderName=None
    if current_game.bid_winner is not None:
        bidderName=current_game.players[current_game.bid_winner].name
    state = {
      "computer_count": len(comp.hand),
      "your_cards": your_cards,
      "kitty": kitty_data,
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
      "show_kitty_confirm": (current_game.bid_winner==0 and current_game.kitty_revealed),
      "game_over": current_game.game_over
    }
    return jsonify(state)

@app.route("/user_draw", methods=["POST"])
def user_draw():
    global current_game
    data=request.get_json() or {}
    discList=data.get("discards",[])
    user=current_game.players[0]
    removed=[]
    for d in discList:
        for c in user.hand:
            if str(c)==d:
                removed.append(c)
                break
    for c in removed:
        user.hand.remove(c)
    new_cards=current_game.deck.deal(len(removed))
    user.hand.extend(new_cards)
    # We can also log how many user discards. But to keep it simpler, we won't store in show_state.
    return jsonify({"message":f"Discarded {len(removed)} card(s), drew {len(new_cards)}."})

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
    # if user is bidder => user sees kitty => user discards => comp discards
    return jsonify({"message":f"Trump suit set to {current_game.trump_suit}"})

@app.route("/finalize_kitty", methods=["POST"])
def finalize_kitty():
    global current_game
    data=request.get_json() or {}
    keepArr=data.get("keep",[])
    discardArr=data.get("discard",[])
    r=current_game.finalize_kitty_selection(keepArr, discardArr)
    return jsonify({"message":"Kitty selection finalized","details":r})

@app.route("/play_card_user", methods=["POST"])
def play_card_user():
    global current_game
    data=request.get_json() or {}
    cardName=data.get("card_name")
    if not cardName:
        return jsonify({"error":"No card provided"}),400
    outcome = current_game.play_trick_user(cardName)
    return jsonify({"message":outcome})

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
