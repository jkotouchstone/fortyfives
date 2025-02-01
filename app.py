import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                           CARD RANK LOOKUPS                                 #
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
    """
    Returns an int rank for card_str under trump_suit.
    """
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
#                              CARD BACK HELPER                               #
###############################################################################
def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    """
    Convert '10 of Hearts' => 'https://deckofcardsapi.com/static/img/0H.png'
    """
    parts=card_str.split(" of ")
    if len(parts)!=2:
        return card_back_url()
    rank, suit=parts
    rank_code="0" if rank=="10" else rank.upper()[0]
    suit_code=suit[0].upper()
    return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

###############################################################################
#                        CLASSES: Card, Deck, Player, Game                    #
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
        # 3 each, kitty(3), 2 each
        first_bidder=0 if self.dealer==1 else 1
        self.players[first_bidder].add_to_hand(self.deck.deal(3))
        self.players[self.dealer].add_to_hand(self.deck.deal(3))
        self.kitty.extend(self.deck.deal(3))
        self.players[first_bidder].add_to_hand(self.deck.deal(2))
        self.players[self.dealer].add_to_hand(self.deck.deal(2))

    def user_bid(self,bid_val):
        """
        If user is first => user picks from [0,15,20,25,30].
          If user picks 30 => user auto-wins the bid.
          Else computer tries to outbid or pass.
        If user is second => computer has chosen a partial bid, user can outbid or pass, etc.
        We'll do a simplified approach:
          - If user picks 30, user instantly wins.
          - Otherwise, comp picks from [pass(0), 15, 20, 25, 30 but must exceed user].
            If it does, comp wins, otherwise user wins. 
        If both pass => dealer forced 15.
        """
        if self.bidding_done:
            return "Bidding is done."

        first_bidder=0 if self.dealer==1 else 1
        if first_bidder==0:
            # user is first
            if bid_val==30:
                self.bid_winner=0
                self.bid=30
            else:
                # user picks e.g. pass(0), 15, 20, 25
                # computer tries to outbid if possible
                # let's have a small array of comp choices that are strictly > user's bid if possible
                comp_options=[]
                for c in [0,15,20,25,30]:
                    if c>bid_val:
                        comp_options.append(c)
                if not comp_options:
                    # comp can't outbid => user wins
                    self.bid_winner=0
                    self.bid=bid_val if bid_val>0 else 15  # if pass => forced 15 to user if user is dealer else? 
                else:
                    comp_choice=random.choice(comp_options)
                    # if both pass => forced dealer 15, but we handled that if user is pass
                    if comp_choice>0:
                        self.bid_winner=1
                        self.bid=comp_choice
                    else:
                        # comp pass => user wins
                        if bid_val>0:
                            self.bid_winner=0
                            self.bid=bid_val
                        else:
                            # both pass => forced dealer 15
                            self.bid_winner=self.dealer
                            self.bid=15
            self.bidding_done=True
        else:
            # user is second => computer was first
            # let's say computer picks random from [0,15,20,25,30].
            comp_first=random.choice([0,15,20,25,30])
            if comp_first==30:
                self.bid_winner=0  # comp instantly wins
                self.bid=30
                self.bidding_done=True
                return "Computer bid 30 and wins."
            else:
                # user can outbid if possible
                if bid_val>comp_first:
                    self.bid_winner=1
                    self.bid=bid_val
                elif bid_val==comp_first and comp_first>0:
                    # tie => second bidder (user) wins
                    self.bid_winner=1
                    self.bid=bid_val
                else:
                    # comp wins
                    self.bid_winner=0
                    self.bid=comp_first if comp_first>0 else 15
            self.bidding_done=True
        return "Bidding concluded"

    def set_trump(self, suit=None):
        if self.bid_winner==1 and self.dealer==1:
            # comp picks automatically
            c_hand=self.players[1].hand
            sc={"Hearts":0,"Diamonds":0,"Clubs":0,"Spades":0}
            for c in c_hand:
                sc[c.suit]+=1
            self.trump_suit=max(sc,key=sc.get)
        else:
            self.trump_suit=suit

    def attach_kitty(self):
        if self.bid_winner==1:
            # computer
            comp=self.players[1]
            comp.hand.extend(self.kitty)
            self.kitty.clear()
            def keepTest(x):
                return x.suit==self.trump_suit or (x.suit=="Hearts" and x.rank=="A")
            comp.hand.sort(key=lambda x:(keepTest(x), get_card_rank(str(x),self.trump_suit)), reverse=True)
            while len(comp.hand)>5:
                comp.hand.pop()
        else:
            self.kitty_revealed=True

    def finalize_kitty_selection(self, keep, discard):
        user=self.players[0]
        user.hand=[c for c in user.hand if str(c) not in discard]
        kitty_keep=[]
        leftover=[]
        for c in self.kitty:
            if str(c) in keep:
                kitty_keep.append(c)
            else:
                leftover.append(c)
        user.hand.extend(kitty_keep)
        self.kitty=leftover
        self.kitty_revealed=False

        # if >5 => discard extras
        discards=[]
        while len(user.hand)>5:
            discards.append(str(user.hand.pop()))
        new_cards=self.deck.deal(len(discards))
        user.hand.extend(new_cards)

        # remove kitty images from UI by clearing kitty
        self.kitty.clear()

        return {"discarded": discards,"drawn":[str(c) for c in new_cards]}

    def record_high_card(self, card_obj, player_idx):
        rank_val=get_card_rank(str(card_obj), self.trump_suit)
        if self.highest_card_played is None:
            self.highest_card_played=str(card_obj)
            self.highest_card_owner=player_idx
        else:
            existing_val=get_card_rank(self.highest_card_played,self.trump_suit)
            if rank_val>existing_val:
                self.highest_card_played=str(card_obj)
                self.highest_card_owner=player_idx

    def play_trick_user(self, card_str):
        user=self.players[0]
        if card_str not in [str(x) for x in user.hand]:
            return "Error: Card not in your hand."
        cobj=next(x for x in user.hand if str(x)==card_str)
        user.hand.remove(cobj)

        self.last_played_cards=[(user.name,str(cobj),card_to_image_url(str(cobj)))]
        self.record_high_card(cobj,0)

        if self.leading_player==0:
            # user leads
            comp=self.players[1]
            follow=self.computer_follow(comp, cobj.suit)
            comp.hand.remove(follow)
            self.last_played_cards.append((comp.name,str(follow),card_to_image_url(str(follow))))
            self.record_high_card(follow,1)
            winner=self.evaluate_trick([(0,cobj),(1,follow)])
        else:
            # comp leads
            comp=self.players[1]
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
        return f"Trick played. Winner: {self.players[winner].name}"

    def computer_lead(self,hand):
        hand.sort(key=lambda c:get_card_rank(str(c),self.trump_suit), reverse=True)
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
        trumps=[(pid,c) for(pid,c) in plays if get_card_rank(str(c),self.trump_suit)>=100]
        if trumps:
            (win_pid, win_card)=max(trumps,key=lambda x:get_card_rank(str(x[1]), self.trump_suit))
        else:
            same=[(pid,c) for(pid,c) in plays if c.suit==lead_suit]
            (win_pid, win_card)=max(same,key=lambda x:get_card_rank(str(x[1]), self.trump_suit))
        return win_pid

    def finalize_hand(self):
        """
        30 total points in a hand: 5 per trick(25) + 5 for highest card.
        If bidder fails to meet their bid => subtract the bid from them.
        """
        # +5 to highest card
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5

        # check if bidder met
        bidder = self.players[self.bid_winner]
        # bidder gets 5*theirTricks +5 if they had highest
        points_earned = bidder.tricks_won*5
        if self.highest_card_owner==self.bid_winner:
            points_earned+=5
        if points_earned<self.bid:
            bidder.score-=self.bid

        # rotate dealer
        self.rotate_dealer()

        return {
          "tricks_points":[p.tricks_won*5 for p in self.players],
          "highest_card":self.highest_card_played,
          "highest_owner": self.players[self.highest_card_owner].name if self.highest_card_owner is not None else None,
          "scores":[self.players[0].score, self.players[1].score]
        }

###############################################################################
#                           FLASK ROUTES / UI                                 #
###############################################################################
current_game=None
tricks_this_hand=0

@app.route("/",methods=["GET"])
def index():
    """
    Updated HTML with the kitty area at 'bottom:200px' and the scoreboard
    moved so it doesn't overlap player's hand. Also includes a 
    '© O'Donohue Software' at bottom.
    """
    html = """
<!DOCTYPE html>
<html>
<head>
  <title>Forty-Fives - with Enhanced Bidding & Layout</title>
  <style>
    body { margin:0; padding:0; background:darkgreen; font-family:sans-serif; color:white; }
    #table { position:relative; width:100%; height:100vh; }

    #controls {
      position:absolute; top:0; left:0; width:100%; text-align:center;
      background: rgba(0,0,0,0.5); padding:10px;
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
      position:absolute; left:20px; bottom:200px; /* moved up from 100px */
      width:200px; text-align:center;
    }
    #biddingArea {
      position:absolute; left:20px; bottom:20px; 
      width:200px; background:rgba(0,0,0,0.3); padding:8px; border-radius:4px;
    }
    #deckArea {
      position:absolute; right:20px; top:50%; transform:translateY(-50%); text-align:center;
    }
    #centerArea {
      position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;
    }
    #scoreboard {
      position:absolute; top:0; right:0; /* moved scoreboard top so it doesn't overlap player hand */
      background:rgba(255,255,255,0.8); color:black; 
      padding:10px; margin:10px; border-radius:5px;
    }
    .card { width:80px; margin:5px; cursor:pointer; border-radius:5px; }
    .selected { outline:2px solid yellow; }
    button { margin:5px; padding:5px 10px; border:none; border-radius:4px; background:#555; color:white; cursor:pointer; }
    button:hover { background:#666; }
    #logArea {
      position:absolute; left:50%; top:65%; transform:translate(-50%,0);
      width:400px; max-height:150px; overflow-y:auto; background:rgba(0,0,0,0.3); padding:8px;
    }
    footer {
      position:absolute; bottom:0; right:0;
      font-size:0.8em; color:#aaa; padding:5px;
    }
  </style>
</head>
<body>
<div id="table">
  <div id="controls">
    <button onclick="newHand()">New Hand</button>
    <button onclick="finalizeHand()">Finalize Hand</button>
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
      <button onclick="selectTrump('Hearts')">Hearts</button>
      <button onclick="selectTrump('Diamonds')">Diamonds</button>
      <button onclick="selectTrump('Clubs')">Clubs</button>
      <button onclick="selectTrump('Spades')">Spades</button>
    </div>
  </div>

  <div id="deckArea">
    <h3>Deck</h3>
    <img id="deckImg" class="card" src="">
    <div id="deckCount"></div>
  </div>

  <div id="scoreboard">
    <h3>Score Notebook</h3>
    <div id="scoreInfo"></div>
  </div>

  <div id="logArea"></div>

  <footer>© O'Donohue Software</footer>
</div>

<script>
let gameState={};
let selectedKitty=[];

function log(msg){
  let logDiv=document.getElementById('logArea');
  let p=document.createElement('p');
  p.textContent=msg;
  logDiv.appendChild(p);
  logDiv.scrollTop=logDiv.scrollHeight;
}

function newHand(){
  fetch('/new_hand',{method:'POST'})
   .then(r=>r.json())
   .then(d=>{
     log(d.message);
     showState();
   });
}

function finalizeHand(){
  fetch('/finalize_hand',{method:'POST'})
   .then(r=>r.json())
   .then(d=>{
     if(d.error){
       log(d.error);
     }else{
       log("Hand Finalized => " + JSON.stringify(d));
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
     updateDealer(d.dealer);
     updateComputerHand(d.computer_count,d.card_back);
     updatePlayerHand(d.your_cards);
     updateKitty(d);
     updateDeck(d);
     updateTrick(d.last_trick);
     updateScores(d);
     updateBiddingUI(d);
   });
}

function updateDealer(dealerName){
  document.getElementById('dealerLabel').textContent = "Dealer: " + dealerName;
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
  selectedKitty=selectedKitty.filter(x=> d.kitty.map(k=>k.name).includes(x)); 
  document.getElementById('confirmKittyBtn').style.display= d.show_kitty_confirm? "inline-block":"none";
  if(d.kitty_revealed){
    d.kitty.forEach(kcard=>{
      let img=document.createElement('img');
      img.src=kcard.img;
      img.className="card";
      img.onclick=()=>{
        if(selectedKitty.includes(kcard.name)) {
          selectedKitty=selectedKitty.filter(x=>x!==kcard.name);
        } else {
          selectedKitty.push(kcard.name);
        }
        updateKitty(d);
      };
      if(selectedKitty.includes(kcard.name)){
        img.classList.add('selected');
      }
      kd.appendChild(img);
    });
  } else {
    // face-down or empty
    d.kitty.forEach(_=>{
      let img=document.createElement('img');
      img.src=d.card_back;
      img.className="card";
      kd.appendChild(img);
    });
  }
}

function confirmKitty(){
  fetch('/finalize_kitty',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({keep:selectedKitty, discard:[]})
  })
   .then(r=>r.json())
   .then(res=>{
     log(res.message);
     selectedKitty=[];
     showState();
   });
}

function updateDeck(d){
  document.getElementById('deckImg').src=d.card_back;
  document.getElementById('deckCount').textContent="Remaining: "+ d.deck_count;
}

function updateTrick(trickCards){
  let t=document.getElementById('trickArea');
  t.innerHTML="";
  if(trickCards && trickCards.length>0){
    trickCards.forEach(item=>{
      let [pname,cardName,cardImg] = item;
      let img=document.createElement('img');
      img.src=cardImg;
      img.className="card";
      t.appendChild(img);
    });
  }
}

function updateScores(d){
  let s=document.getElementById('scoreInfo');
  s.innerHTML = "Trick Points - You: "+ d.round_score_your +", Computer: "+ d.round_score_comp
    + "<br>Total: You "+ d.total_your + ", Computer "+ d.total_comp;
}

function updateBiddingUI(d){
  let bdiv=document.getElementById('bidButtons');
  bdiv.innerHTML="";
  let tdiv=document.getElementById('trumpButtons');
  tdiv.style.display= d.trump_set? "none":"none";

  if(!d.bidding_done){
    // user can pick from pass(0),15,20,25,30
    // once user picks, we run the logic on server
    // if user is first => computer tries to outbid 
    // if user is second => computer has a partial
    // We'll simply show [Pass,15,20,25,30]
    // If user picks 30 => user automatically wins
    // The server logic will handle the rest
    let opts=[0,15,20,25,30];
    opts.forEach(o=>{
      let label = (o===0)?"Pass":"Bid "+o;
      let btn=makeBidBtn(label,o);
      bdiv.appendChild(btn);
    });
  } else {
    // bidding done => if user is bidder & no trump => show trump
    if(d.bidder=="You" && !d.trump_set){
      tdiv.style.display="block";
    }
  }
}

function makeBidBtn(label,val){
  let btn=document.createElement('button');
  btn.textContent=label;
  btn.onclick=()=>{
    fetch('/user_bid',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({bid_val: val})
    })
     .then(r=>r.json())
     .then(dd=>{
       log(dd.message);
       showState();
     });
  };
  return btn;
}

function selectTrump(suit){
  fetch('/pick_trump',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({suit})
  })
   .then(r=>r.json())
   .then(resp=>{
     log(resp.message);
     showState();
   });
}

function playCard(name){
  fetch('/play_card_user',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({card_name:name})
  })
   .then(r=>r.json())
   .then(dd=>{
     log(dd.message);
     showState();
   });
}

window.onload=()=>{ showState(); };
</script>
</body>
</html>
    """
    return html

###############################################################################
#                           HAND LOGIC ROUTES                                 #
###############################################################################
current_game=None
tricks_this_hand=0

@app.route("/new_hand", methods=["POST"])
def new_hand_api():
    global current_game, tricks_this_hand
    if not current_game:
        current_game=Game()
    else:
        current_game.reset_hand()
    current_game.deal_hands()
    tricks_this_hand=0
    return jsonify({"message":"New hand dealt."})

@app.route("/finalize_hand", methods=["POST"])
def finalize_hand_api():
    global current_game, tricks_this_hand
    if tricks_this_hand<5:
        return jsonify({"error":"Not all 5 tricks have been played."}),400
    res=current_game.finalize_hand()
    return jsonify(res)

###############################################################################
#                         BIDDING & TRUMP ROUTES                              #
###############################################################################
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
    st=data.get("suit","Hearts")
    current_game.set_trump(st)
    current_game.attach_kitty()
    return jsonify({"message":f"Trump suit set to {current_game.trump_suit}"})

@app.route("/finalize_kitty", methods=["POST"])
def finalize_kitty():
    global current_game
    data=request.get_json() or {}
    keepArr=data.get("keep",[])
    discArr=data.get("discard",[])
    r=current_game.finalize_kitty_selection(keepArr, discArr)
    return jsonify({"message":"Kitty selection finalized","details":r})

###############################################################################
#                         TRICK PLAY ROUTES                                   #
###############################################################################
@app.route("/play_card_user", methods=["POST"])
def play_card_user():
    global current_game, tricks_this_hand
    data=request.get_json() or {}
    cName=data.get("card_name")
    if not cName:
        return jsonify({"error":"No card."}),400
    out=current_game.play_trick_user(cName)
    if not out.startswith("Error"):
        tricks_this_hand+=1
    return jsonify({"message":out})

###############################################################################
#                             SHOW STATE ROUTE                                #
###############################################################################
@app.route("/show_state", methods=["GET"])
def show_state_api():
    global current_game
    if not current_game:
        return jsonify({"error":"No game in progress"}),400
    user=current_game.players[0]
    comp=current_game.players[1]

    your_cards=[{"name":str(c),"img":card_to_image_url(str(c))} for c in user.hand]
    kitty_data=[{"name":str(c),"img":card_to_image_url(str(c))} for c in current_game.kitty]

    bid_submitted = (current_game.bid_winner is not None)
    trump_set = (current_game.trump_suit is not None)
    show_kitty_confirm = (current_game.bid_winner==0 and current_game.kitty_revealed)

    bidderName=None
    if current_game.bid_winner is not None:
        bidderName = current_game.players[current_game.bid_winner].name

    state={
      "dealer": current_game.players[current_game.dealer].name,
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
      "bid_submitted": bid_submitted,
      "bidding_done": current_game.bidding_done,
      "trump_set": trump_set,
      "show_kitty_confirm": show_kitty_confirm
    }
    return jsonify(state)


if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
