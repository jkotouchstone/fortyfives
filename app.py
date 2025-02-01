import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                           CARD RANKS FOR FORTY-FIVES                        #
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
    if trump_suit == "Diamonds":
        if card_str in TRUMP_DIAMONDS:
            return TRUMP_DIAMONDS[card_str]
        else:
            if card_str.endswith("Hearts"):
                return OFFSUIT_HEARTS.get(card_str, 0)
            elif card_str.endswith("Clubs"):
                return OFFSUIT_CLUBS.get(card_str, 0)
            elif card_str.endswith("Spades"):
                return OFFSUIT_SPADES.get(card_str, 0)
            else:
                return 0
    elif trump_suit == "Hearts":
        if card_str in TRUMP_HEARTS:
            return TRUMP_HEARTS[card_str]
        else:
            if card_str.endswith("Diamonds"):
                return OFFSUIT_DIAMONDS.get(card_str, 0)
            elif card_str.endswith("Clubs"):
                return OFFSUIT_CLUBS.get(card_str, 0)
            elif card_str.endswith("Spades"):
                return OFFSUIT_SPADES.get(card_str, 0)
            else:
                return 0
    elif trump_suit == "Clubs":
        if card_str in TRUMP_CLUBS:
            return TRUMP_CLUBS[card_str]
        else:
            if card_str.endswith("Diamonds"):
                return OFFSUIT_DIAMONDS.get(card_str, 0)
            elif card_str.endswith("Hearts"):
                return OFFSUIT_HEARTS.get(card_str, 0)
            elif card_str.endswith("Spades"):
                return OFFSUIT_SPADES.get(card_str, 0)
            else:
                return 0
    elif trump_suit == "Spades":
        if card_str in TRUMP_SPADES:
            return TRUMP_SPADES[card_str]
        else:
            if card_str.endswith("Diamonds"):
                return OFFSUIT_DIAMONDS.get(card_str, 0)
            elif card_str.endswith("Hearts"):
                return OFFSUIT_HEARTS.get(card_str, 0)
            elif card_str.endswith("Clubs"):
                return OFFSUIT_CLUBS.get(card_str, 0)
            else:
                return 0
    return 0

###############################################################################
#                       CARD IMAGE (deckofcardsapi.com)                       #
###############################################################################
def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    parts = card_str.split(" of ")
    if len(parts)!=2:
        return card_back_url()
    rank, suit = parts
    suit_letter = suit[0].upper()
    rank_code = "0" if rank=="10" else rank.upper()[0]
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_letter}.png"

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
        suits = ["Hearts","Diamonds","Clubs","Spades"]
        ranks = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
        self.cards = [Card(s,r) for s in suits for r in ranks]
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self,n):
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

class Player:
    def __init__(self,name):
        self.name = name
        self.hand = []
        self.score = 0
        self.tricks_won = 0
    def add_to_hand(self,cards):
        self.hand.extend(cards)

class Game:
    def __init__(self):
        self.players = [Player("You"), Player("Computer")]
        self.dealer = 1  # 0=You,1=Computer
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card = None
        self.highest_owner = None
        self.last_played_cards = []
        self.kitty_revealed = False
        self.bidding_done = False  # track if we've finished bidding

    def rotate_dealer(self):
        self.dealer = 1 - self.dealer

    def reset_round_state(self):
        self.deck = Deck()
        self.kitty.clear()
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card = None
        self.highest_owner = None
        self.last_played_cards = []
        self.kitty_revealed = False
        self.bidding_done = False
        for p in self.players:
            p.hand.clear()
            p.tricks_won = 0

    def deal_hands(self):
        self.deck.shuffle()
        for p in self.players:
            p.hand.clear()
        self.kitty.clear()
        # For two players:
        # The "non-dealer" is the first bidder
        first_bidder = 0 if self.dealer==1 else 1
        # 3 each, then kitty(3), then 2 each
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self,bid_val):
        # The user (maybe first or second bidder) picks a bid via UI
        # If user is first bidder, the computer responds. If user is second bidder (the dealer), we have the comp's first bid stored in memory or we do it on the fly.
        # Let's store "pendingComputerBid" in memory or do it immediately. We'll do an approach:
        if self.bidding_done:
            return "Bidding already concluded."

        # figure out if user is first or second bidder
        first_bidder = 0 if self.dealer==1 else 1
        if first_bidder == 0:
            # user is first bidder
            user_first_bid = bid_val  # 0=pass, 15,20, etc.
            # then computer responds (never more than 20).
            comp_options = [0,20]  # pass or 20 if comp is dealer or forced
            # if user bids 15, comp can pass or 20
            # if user passes(0), comp can auto-15 if it's the dealer, but let's keep it simpler:
            # We'll do:
            comp_decision = random.choice(comp_options)
            # compare
            if user_first_bid>comp_decision:
                self.bid_winner = 0
                self.bid = user_first_bid
            elif comp_decision>0:
                self.bid_winner = 1
                self.bid = comp_decision
            else:
                # both pass => dealer forced 15
                # if dealer is the computer => comp is second bidder => forced 15
                if self.dealer==1:
                    self.bid_winner = 1
                    self.bid = 15
                else:
                    self.bid_winner = 0
                    self.bid = 15
            self.bidding_done = True
        else:
            # user is second bidder => first bidder was the computer
            # computer can do pass(0) or 20 randomly
            comp_bid = random.choice([0,20])
            # now user must respond with "pass or match 20" if comp bid 20, or if comp pass => user forced 15 if they pass also
            # We interpret "bid_val" as the user's final.
            if comp_bid>0:
                # comp bid 20 => user can pass or 20
                if bid_val>0:  # user matches 20
                    # tie => second bidder wins => user
                    self.bid_winner = 1
                    self.bid = bid_val
                else:
                    # user pass => comp wins
                    self.bid_winner = 0
                    self.bid = comp_bid
            else:
                # comp pass => user can do pass => forced 15 or user can pick 15
                if bid_val>0:
                    self.bid_winner = 1
                    self.bid = bid_val
                else:
                    # both pass => second bidder is user => forced 15
                    self.bid_winner = 1
                    self.bid = 15
            self.bidding_done = True

    def set_trump(self, suit=None):
        if self.bid_winner==1 and self.dealer==1:
            # computer picks automatically
            c_hand = self.players[1].hand
            suit_ct = {"Hearts":0,"Diamonds":0,"Clubs":0,"Spades":0}
            for c in c_hand:
                suit_ct[c.suit]+=1
            self.trump_suit = max(suit_ct,key=suit_ct.get)
        else:
            self.trump_suit = suit

    def attach_kitty(self):
        # if comp is bidder => auto gather
        if self.bid_winner==1:
            comp = self.players[1]
            comp.hand.extend(self.kitty)
            self.kitty.clear()
            def keep(c):
                return c.suit==self.trump_suit or (c.suit=="Hearts" and c.rank=="A")
            comp.hand.sort(key=lambda x:(keep(x), get_card_rank(str(x),self.trump_suit)),reverse=True)
            while len(comp.hand)>5:
                comp.hand.pop()
        else:
            # user
            self.kitty_revealed = True

    def finalize_kitty_selection(self, keep_kitty, discard_hand):
        # user is bidder
        user = self.players[0]
        user.hand = [c for c in user.hand if str(c) not in discard_hand]
        to_keep = []
        leftover = []
        for c in self.kitty:
            if str(c) in keep_kitty:
                to_keep.append(c)
            else:
                leftover.append(c)
        user.hand.extend(to_keep)
        self.kitty = leftover
        self.kitty_revealed=False

        # if >5 => discard extras
        discards = []
        while len(user.hand)>5:
            discards.append(str(user.hand.pop()))
        new_cards = self.deck.deal(len(discards))
        user.hand.extend(new_cards)
        return {"discarded":discards,"drawn":[str(c) for c in new_cards]}

    def play_trick_user(self, card_str):
        user = self.players[0]
        if card_str not in [str(c) for c in user.hand]:
            return "Error: Card not in your hand."
        played = next(c for c in user.hand if str(c)==card_str)
        user.hand.remove(played)

        self.last_played_cards = [(user.name, str(played), card_to_image_url(str(played)))]
        if self.leading_player==0:
            # user leads => computer follows
            comp = self.players[1]
            follow = self.computer_follow(comp, played.suit)
            comp.hand.remove(follow)
            self.last_played_cards.append((comp.name, str(follow), card_to_image_url(str(follow))))
            winner = self.evaluate_trick([(0, played),(1, follow)])
        else:
            # comp leads => user follows
            comp = self.players[1]
            lead = self.computer_lead(comp.hand)
            comp.hand.remove(lead)
            self.last_played_cards = [
                (comp.name,str(lead),card_to_image_url(str(lead))),
                (user.name,str(played),card_to_image_url(str(played)))
            ]
            winner = self.evaluate_trick([(1,lead),(0,played)])
        self.players[winner].score +=5
        self.players[winner].tricks_won+=1
        self.leading_player=winner
        return f"Trick played. Winner: {self.players[winner].name}"

    def computer_lead(self, hand):
        hand.sort(key=lambda x: get_card_rank(str(x),self.trump_suit), reverse=True)
        return hand[0] if hand else None

    def computer_follow(self, comp, lead_suit):
        valid = [c for c in comp.hand if c.suit==lead_suit]
        if valid:
            valid.sort(key=lambda x: get_card_rank(str(x),self.trump_suit))
            return valid[0]
        else:
            comp.hand.sort(key=lambda x:get_card_rank(str(x),self.trump_suit))
            return comp.hand[0]

    def evaluate_trick(self, plays):
        lead_suit = plays[0][1].suit
        trump_cards = [(pid,c) for (pid,c) in plays if get_card_rank(str(c),self.trump_suit)>=100]
        if trump_cards:
            (win_pid, win_card) = max(trump_cards, key=lambda x:get_card_rank(str(x[1]),self.trump_suit))
        else:
            same = [(pid,c) for (pid,c) in plays if c.suit==lead_suit]
            (win_pid, win_card) = max(same, key=lambda x:get_card_rank(str(x[1]),self.trump_suit))
        return win_pid

    def finalize_round(self):
        # highest card gets +5
        # we haven't tracked the single highest card each trick. Let's do a simpler approach or skip?
        # We'll skip it for brevity or do a partial approach:
        # Actually let's skip the extra logic for "highest card." We'll just finalize.
        round_scores = [p.tricks_won*5 for p in self.players]
        # if bidder didn't meet bid => subtract from their total
        if round_scores[self.bid_winner]<self.bid:
            self.players[self.bid_winner].score-=self.bid
            round_scores[self.bid_winner] = -self.bid
        # rotate dealer for next round
        self.rotate_dealer()
        return {
            "round_scores": round_scores,
            "total_scores": [self.players[0].score,self.players[1].score]
        }

###############################################################################
#                                FLASK ROUTES                                 #
###############################################################################
current_game = None
round_tricks=0

@app.route("/", methods=["GET"])
def index():
    """
    Single HTML with no 'Refresh' or 'Rotate Dealer' button, and bidding/trump UI
    placed in lower-left (with clickable buttons).
    """
    html = """
<!DOCTYPE html>
<html>
<head>
  <title>Forty-Fives Table</title>
  <style>
    body { margin:0; padding:0; background:darkgreen; font-family: sans-serif; color:white; }
    #table { position: relative; width:100%; height:100vh; }

    #controls {
      position:absolute; top:0; left:0; width:100%; text-align:center;
      background: rgba(0,0,0,0.5); padding:10px;
    }

    #computerArea {
      position: absolute; left:50%; transform:translateX(-50%);
      top:80px; text-align:center;
    }
    #playerArea {
      position:absolute; left:50%; transform:translateX(-50%);
      bottom:20px; text-align:center;
    }
    #kittyArea {
      position:absolute; left: 20px; bottom: 100px;
      width:200px; text-align:center;
    }
    #biddingArea {
      position:absolute; left:20px; bottom:20px;
      width:200px; background: rgba(0,0,0,0.3); padding:8px; border-radius:4px;
    }
    #deckArea {
      position:absolute; right:20px; top:50%; transform:translateY(-50%); text-align:center;
    }
    #centerArea {
      position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
      text-align:center;
    }
    #scoreboard {
      position:absolute; bottom:0; right:0;
      background:rgba(255,255,255,0.8); color:black; padding:10px; margin:10px; border-radius:5px;
    }
    .card { width:80px; margin:5px; cursor:pointer; border-radius:5px; }
    .selected { outline:2px solid yellow; }
    #log { position:absolute; left:50%; top:65%; transform:translate(-50%,0);
           width:400px; max-height:150px; overflow-y:auto; background:rgba(0,0,0,0.3); padding:8px; }
    button { margin:5px; padding:5px 10px; border:none; border-radius:4px; background:#555; color:white; cursor:pointer; }
    button:hover { background:#666; }
  </style>
</head>
<body>
<div id="table">
  <div id="controls">
    <button onclick="newRound()">New Round</button>
    <button onclick="finalizeRound()">Finalize Round</button>
    <span id="dealerLabel"></span>
  </div>
  <div id="computerArea">
    <h3>Computer's Hand</h3>
    <div id="computerHand"></div>
  </div>
  <div id="centerArea">
    <h3>Current Trick</h3>
    <div id="trickArea"></div>
  </div>
  <div id="playerArea">
    <h3>Your Hand</h3>
    <div id="playerHand"></div>
  </div>
  <div id="kittyArea">
    <h3>Kitty</h3>
    <div id="kittyDisplay"></div>
    <button id="confirmKittyBtn" style="display:none" onclick="confirmKitty()">Confirm Kitty</button>
  </div>
  <div id="biddingArea">
    <h3>Bidding / Trump</h3>
    <div id="bidButtons"></div>
    <div id="trumpButtons" style="display:none">
      <p>Select Trump:</p>
      <button onclick="pickTrump('Hearts')">Hearts</button>
      <button onclick="pickTrump('Diamonds')">Diamonds</button>
      <button onclick="pickTrump('Clubs')">Clubs</button>
      <button onclick="pickTrump('Spades')">Spades</button>
    </div>
  </div>
  <div id="deckArea">
    <h3>Deck</h3>
    <img id="deckImg" class="card" src="" />
    <div id="deckCount"></div>
  </div>
  <div id="scoreboard">
    <h3>Score Notebook</h3>
    <div id="scoreInfo"></div>
  </div>
  <div id="log"></div>
</div>

<script>
let selectedKitty=[];
let selectedDiscards=[];
let gameState={};

function log(msg){
  let logDiv = document.getElementById('log');
  let p = document.createElement('p');
  p.textContent = msg;
  logDiv.appendChild(p);
  logDiv.scrollTop = logDiv.scrollHeight;
}

function newRound(){
  fetch('/new_round',{method:'POST'})
   .then(r=>r.json())
   .then(d=>{
     log(d.message);
     showState();
   });
}

function finalizeRound(){
  fetch('/finalize_round',{method:'POST'})
   .then(r=>r.json())
   .then(d=>{
     if(d.error){
       log(d.error);
     }else{
       log("Round finalized => Scores: " + JSON.stringify(d));
     }
     showState();
   });
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
     updateDealerLabel(d.dealer);
     updateComputerHand(d.computer_count,d.card_back);
     updatePlayerHand(d.your_cards);
     updateKitty(d);
     updateDeck(d);
     updateTrick(d.last_trick);
     updateScoreboard(d);
     updateBiddingUI(d);
   });
}

function updateDealerLabel(dealerName){
  document.getElementById('dealerLabel').textContent = "Dealer: " + dealerName;
}

function updateComputerHand(count, backUrl){
  let ch = document.getElementById('computerHand');
  ch.innerHTML="";
  for(let i=0;i<count;i++){
    let img=document.createElement('img');
    img.src=backUrl;
    img.className="card";
    ch.appendChild(img);
  }
}

function updatePlayerHand(cards){
  let ph = document.getElementById('playerHand');
  ph.innerHTML="";
  cards.forEach(c=>{
    let img=document.createElement('img');
    img.src=c.img;
    img.className="card";
    img.onclick=()=>playCard(c.name);
    ph.appendChild(img);
  });
}

function updateKitty(d){
  let kd=document.getElementById('kittyDisplay');
  kd.innerHTML="";
  document.getElementById('confirmKittyBtn').style.display = d.show_kitty_confirm?"inline-block":"none";
  if(d.kitty_revealed){
    d.kitty.forEach(c=>{
      let img=document.createElement('img');
      img.src=c.img;
      img.className="card";
      img.onclick=()=>{
        if(selectedKitty.includes(c.name)){
          selectedKitty=selectedKitty.filter(x=>x!==c.name);
        }else{
          selectedKitty.push(c.name);
        }
        updateKitty(d);
      };
      if(selectedKitty.includes(c.name)){
        img.classList.add('selected');
      }
      kd.appendChild(img);
    });
  }else{
    for(let i=0;i<d.kitty.length;i++){
      let img=document.createElement('img');
      img.src=d.card_back;
      img.className="card";
      kd.appendChild(img);
    }
  }
}

function updateDeck(d){
  document.getElementById('deckImg').src=d.card_back;
  document.getElementById('deckCount').textContent="Remaining: "+d.deck_count;
}

function updateTrick(lastTrick){
  let t=document.getElementById('trickArea');
  t.innerHTML="";
  if(lastTrick && lastTrick.length>0){
    lastTrick.forEach(item=>{
      let [pname, cstr, cimg] = item;
      let img=document.createElement('img');
      img.src=cimg;
      img.className="card";
      t.appendChild(img);
    });
  }
}

function updateScoreboard(d){
  let s=document.getElementById('scoreInfo');
  s.innerHTML=`Round Score - You:${d.round_score_your}, Computer:${d.round_score_comp}<br>
   Total: You ${d.total_your}, Computer ${d.total_comp}`;
}

function updateBiddingUI(d){
  let bidDiv=document.getElementById('bidButtons');
  bidDiv.innerHTML="";
  let trumpDiv=document.getElementById('trumpButtons');
  trumpDiv.style.display=(d.trump_set?"none":"none");

  if(!d.bid_submitted){
    // user hasn't placed final bid => show clickable options
    // figure out if user is first or second bidder
    let firstBidder=(d.dealer=="Computer")?0:1; 
    // if user is first bidder => possible bids: [15,20,Pass]
    // if user is second bidder => depends on comp's random. Let's handle it simpler:
    // We'll just call "/bid" with the chosen value, the code will do the logic.
    // So we show the relevant set of buttons:
    if((firstBidder==0 && d.bid_winner==null) || (firstBidder==1 && d.bid_winner==null)){
      // We haven't done the user bid yet => show [15,20,Pass]
      let b15=makeBidBtn("Bid 15",15);
      let b20=makeBidBtn("Bid 20",20);
      let pass=makeBidBtn("Pass",0);
      bidDiv.appendChild(b15);bidDiv.appendChild(b20);bidDiv.appendChild(pass);
    } else {
      // means user is second bidder => comp presumably made a 20 or pass. 
      // We'll rely on server logic. For simplicity, let's show "Pass" or "Match 20"
      let b20=makeBidBtn("Bid 20",20);
      let pass=makeBidBtn("Pass",0);
      bidDiv.appendChild(b20);bidDiv.appendChild(pass);
    }
  } else {
    // if bid_submitted => check if trump is set
    if(!d.trump_set && d.bid_winner=="You"){
      trumpDiv.style.display="inline-block";
    }
  }
}

function makeBidBtn(label, val){
  let btn=document.createElement('button');
  btn.textContent=label;
  btn.onclick=()=>{
    fetch('/user_bid',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ bid_val: val })
    })
    .then(r=>r.json())
    .then(res=>{
      log(res.message);
      showState();
    });
  };
  return btn;
}

function pickTrump(suit){
  fetch('/pick_trump',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ suit })
  })
   .then(r=>r.json())
   .then(d=>{
     log(d.message);
     showState();
   });
}

function confirmKitty(){
  fetch('/finalize_kitty',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ keep:selectedKitty, discard:[] })
  })
   .then(r=>r.json())
   .then(d=>{
     log(d.message);
     selectedKitty=[];
     showState();
   });
}

function playCard(cName){
  fetch('/play_card_user',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ card_name:cName })
  })
   .then(r=>r.json())
   .then(d=>{
     log(d.message);
     showState();
   });
}

// On load, get initial state
window.onload=()=>{
  showState();
};
</script>
</body>
</html>
    """
    return html

###############################################################################
#                               API ROUTES                                    #
###############################################################################

@app.route("/new_round", methods=["POST"])
def new_round_api():
    global current_game, round_tricks
    if not current_game:
        current_game = Game()
    else:
        current_game.reset_round_state()
    current_game.deal_hands()
    round_tricks=0
    return jsonify({"message":"New round dealt."})

@app.route("/user_bid", methods=["POST"])
def user_bid():
    global current_game
    data=request.get_json() or {}
    bval=data.get("bid_val",0)
    current_game.user_bid(bval)
    return jsonify({"message":"Bidding step done."})

@app.route("/pick_trump", methods=["POST"])
def pick_trump():
    global current_game
    data=request.get_json() or {}
    suit=data.get("suit","Hearts")
    current_game.set_trump(suit)
    # if computer => skip else user => reveal kitty
    current_game.attach_kitty()
    return jsonify({"message":f"Trump set to {current_game.trump_suit}."})

@app.route("/finalize_kitty", methods=["POST"])
def finalize_kitty_api():
    global current_game
    data=request.get_json() or {}
    keep = data.get("keep",[])
    discard = data.get("discard",[])
    res = current_game.finalize_kitty_selection(keep, discard)
    return jsonify({"message":"Kitty selection done","discard_info":res})

@app.route("/play_card_user", methods=["POST"])
def play_card_user():
    global current_game, round_tricks
    data=request.get_json() or {}
    cName=data.get("card_name")
    if not cName:
        return jsonify({"error":"No card."}),400
    msg = current_game.play_trick_user(cName)
    if not msg.startswith("Error"):
        round_tricks+=1
    return jsonify({"message":msg})

@app.route("/finalize_round", methods=["POST"])
def finalize_round_api():
    global current_game, round_tricks
    if round_tricks<5:
        return jsonify({"error":"Not all 5 tricks played."}),400
    res = current_game.finalize_round()
    return jsonify({"scores":res})

@app.route("/show_state", methods=["GET"])
def show_state_api():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}),400
    user = current_game.players[0]
    comp = current_game.players[1]

    your_cards=[{"name":str(c),"img":card_to_image_url(str(c))} for c in user.hand]
    kitty_list=[{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]
    
    bid_submitted = (current_game.bid_winner is not None)
    trump_set = (current_game.trump_suit is not None)
    show_kitty_confirm = (current_game.bid_winner==0 and current_game.kitty_revealed)

    state={
      "dealer": current_game.players[current_game.dealer].name,
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
      "bid_submitted": bid_submitted,
      "trump_set": trump_set,
      "show_kitty_confirm": show_kitty_confirm
    }
    return jsonify(state)

# We'll create or reuse the "current_game" if none
@app.route("/init", methods=["GET"])
def init_game():
    global current_game
    if not current_game:
        current_game=Game()
    return jsonify({"message":"Game inited"})

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
