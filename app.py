import os
import random
import json
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

# This version supports only 45's Heads Up.
current_game = None

#################################
#         GAME CLASSES          #
#################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit      # e.g., "Hearts"
        self.rank = rank      # e.g., "A", "7", etc.

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        # For 45's we use a nonstandard deck. Here we include these ranks.
        ranks = ["2", "3", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        for s in suits:
            for r in ranks:
                self.cards.append(Card(s, r))
        # Ensure the special 5 of Hearts is included.
        if not any(str(c) == "5 of Hearts" for c in self.cards):
            self.cards.append(Card("Hearts", "5"))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

    def draw(self, num_cards):
        return self.deal(num_cards)

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []         # List of Card objects
        self.score = 0
        self.tricks_won = 0
        self.trick_pile = []   # Collected cards from won tricks

    def set_hand(self, cards):
        self.hand = cards

    def add_to_hand(self, cards):
        self.hand.extend(cards)

    def get_hand_strings(self):
        return [str(card) for card in self.hand]

    def discard_auto(self, trump):
        before = len(self.hand)
        # For computer bidder, keep only trump cards.
        self.hand = [card for card in self.hand if card.suit == trump]
        return before - len(self.hand)

class Game:
    def __init__(self):
        # Heads Up: two players ("You" and "Computer")
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []         # 3 cards set aside
        self.trump_suit = None  # To be chosen during trump selection
        self.bid_winner = None  # 0 = human (dealer), 1 = computer
        self.bid = 0            # Winning bid amount
        self.leading_player = None  # Which player leads the trick: 0 or 1
        self.trick_count = 0
        self.trick_log_text = ""
        self.trick_history = []  # List of dicts, one per trick
        self.starting_scores = {p.name: p.score for p in self.players}

    def deal_hands(self):
        self.deck.shuffle()
        self.kitty = self.deck.deal(3)
        for p in self.players:
            p.set_hand([])  # Clear previous hand
            p.tricks_won = 0
            p.trick_pile = []
        for p in self.players:
            p.add_to_hand(self.deck.deal(5))
        self.trick_count = 0
        self.trick_log_text = ""
        self.trick_history = []
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trump_suit = None

    def get_player_hand(self):
        return self.players[0].get_hand_strings()

    def get_dealer(self):
        # In this demo, the human ("You") is always the dealer.
        return self.players[0].name

    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]

    def discard_phase(self, bidder_index, discards):
        # Remove selected discard cards (list of strings) from bidder's hand.
        bidder = self.players[bidder_index]
        initial = len(bidder.hand)
        bidder.hand = [card for card in bidder.hand if str(card) not in discards]
        discarded = initial - len(bidder.hand)
        # Auto-draw to complete hand to 5 cards.
        missing = 5 - len(bidder.hand)
        if missing > 0:
            bidder.add_to_hand(self.deck.draw(missing))
        return {
            "player_hand": self.players[0].get_hand_strings(),
            "discard_count": discarded
        }

    def attach_kitty(self, player_index, keep_list):
        # Add selected kitty cards (by their string) to the bidder's hand.
        bidder = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    bidder.add_to_hand([c])
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        # Ensure hand is exactly 5 cards.
        if len(bidder.hand) > 5:
            bidder.hand = bidder.hand[:5]
        return {
            "player_hand": self.players[0].get_hand_strings()
        }

    def play_trick(self, played_card=None):
        # Basic trick play logic (for demonstration only).
        played = {}
        if self.leading_player == 1:  # Computer leads.
            if played_card is None:
                comp_hand = self.players[1].hand
                if not comp_hand:
                    # If the computer has no cards left, no trick is played
                    return {"trick_result": "Computer has no cards to lead.", 
                            "current_trick_cards": {}}, None
                comp_card = comp_hand.pop(0)
                self.trick_log_text = f"Computer leads with {comp_card}."
                played[1] = comp_card
            else:
                if played_card not in self.get_player_hand():
                    return ({"trick_result": "Invalid card played.",
                             "current_trick_cards": {}}, None)
                human_card = next(card for card in self.players[0].hand if str(card) == played_card)
                self.players[0].hand.remove(human_card)
                played[0] = human_card
                self.trick_log_text = f"You played {human_card}."
            current_trick = {
                "Computer": str(played.get(1)) if played.get(1) else "",
                "You": str(played.get(0)) if played.get(0) else ""
            }
        else:  # Human leads.
            if played_card is None:
                return {"trick_result": "Your turn to lead.",
                        "current_trick_cards": {}}, None
            if played_card not in self.get_player_hand():
                return ({"trick_result": "Invalid card played.",
                         "current_trick_cards": {}}, None)
            human_card = next(card for card in self.players[0].hand if str(card) == played_card)
            self.players[0].hand.remove(human_card)
            played[0] = human_card
            self.trick_log_text = f"You lead with {human_card}."
            comp_hand = self.players[1].hand
            if comp_hand:
                comp_card = comp_hand.pop(0)
                played[1] = comp_card
                self.trick_log_text += f" Computer plays {comp_card}."
            else:
                comp_card = None
                self.trick_log_text += " Computer did not play."
            current_trick = {
                "You": str(played.get(0)) if played.get(0) else "",
                "Computer": str(played.get(1)) if played.get(1) else ""
            }

        # Determine winner (for demo, we simply compare the card strings)
        if played.get(0) is None or played.get(1) is None:
            winner = "You" if played.get(0) else "Computer"
        else:
            # Extremely naive "winner" logic: just compare string (NOT real 45's logic)
            winner = "You" if str(played.get(0)) > str(played.get(1)) else "Computer"

        if winner == "You":
            self.players[0].score += 5
            self.players[0].tricks_won += 1
        else:
            self.players[1].score += 5
            self.players[1].tricks_won += 1

        trick_info = {
            "trick_number": self.trick_count + 1,
            "cards": current_trick,
            "winner": winner
        }
        self.trick_history.append(trick_info)
        # Alternate lead based on trick winner.
        self.leading_player = 0 if winner == "You" else 1
        self.trick_count += 1

        # If we've played 5 tricks or the hand is empty, that ends the hand.
        if self.trick_count >= 5 or len(self.players[0].hand) == 0:
            hand_scores = {
                p.name: p.score - self.starting_scores[p.name]
                for p in self.players
            }
            result_text = (self.trick_log_text +
                           " Hand complete. Last trick won by " +
                           self.trick_history[-1]["winner"] + ".")
            return (
                {
                    "trick_result": result_text,
                    "current_trick_cards": current_trick,
                    "trick_history": self.trick_history
                },
                hand_scores
            )
        else:
            return (
                {
                    "trick_result": self.trick_log_text,
                    "current_trick_cards": current_trick,
                    "trick_winner": winner
                },
                None
            )

#################################
#           ROUTES              #
#################################

# Landing page – game starts immediately.
@app.route("/", methods=["GET"])
def landing():
    global current_game
    current_game = Game()
    current_game.deal_hands()
    dealer = current_game.get_dealer()
    # Render the game UI.
    game_html = (
        "<!DOCTYPE html>"
        "<html lang='en'>"
        "<head>"
        "  <meta charset='UTF-8'>"
        "  <title>45's Heads Up</title>"
        "  <link rel='icon' href='https://deckofcardsapi.com/static/img/5_of_clubs.png' type='image/png'>"
        "  <style>"
        "    body { font-family: Arial, sans-serif; background-color: #35654d; color: #fff; text-align: center; }"
        "    #gameContainer { max-width: 1000px; margin: 50px auto; padding: 20px; background-color: #2e4e41; border-radius: 10px; }"
        "    .btn { padding: 10px 20px; font-size: 16px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }"
        "    .card-row { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }"
        "    .card-image { width: 100px; }"
        "    .selected-card { border: 2px solid #f1c40f; }"
        "    .section { margin: 20px 0; display: none; }"
        "  </style>"
        "</head>"
        "<body>"
        "  <div id='gameContainer'>"
        "    <h1>45's Heads Up</h1>"
        "    <!-- Added trump display element -->"
        "    <div id='trumpDisplay' style='margin-bottom: 20px;'></div>"
        "    <p>Dealer: <span id='dealer'>" + dealer + "</span></p>"
        "    <h2>Your Hand:</h2>"
        "    <div id='hand' class='card-row'></div>"
        "    <!-- Bidding Section -->"
        "    <div id='biddingSection' class='section'>"
        "      <h2>Bidding</h2>"
        "      <p id='computerBid'></p>"
        "      <div id='bidButtons'>"
        "        <button class='btn bidButton' data-bid='0'>Pass</button>"
        "        <button class='btn bidButton' data-bid='15'>15</button>"
        "        <button class='btn bidButton' data-bid='20'>20</button>"
        "        <button class='btn bidButton' data-bid='25'>25</button>"
        "        <button class='btn bidButton' data-bid='30'>30</button>"
        "      </div>"
        "      <p id='bidError'></p>"
        "    </div>"
        "    <!-- Trump Selection Section -->"
        "    <div id='trumpSelectionSection' class='section'>"
        "      <h2>Select Trump Suit</h2>"
        "      <div style='display: flex; justify-content: center; gap: 20px;'>"
        "        <button class='btn trumpButton' data-suit='Hearts' style='background-color:#e74c3c;'>♥</button>"
        "        <button class='btn trumpButton' data-suit='Diamonds' style='background-color:#f1c40f;'>♦</button>"
        "        <button class='btn trumpButton' data-suit='Clubs' style='background-color:#27ae60;'>♣</button>"
        "        <button class='btn trumpButton' data-suit='Spades' style='background-color:#2980b9;'>♠</button>"
        "      </div>"
        "    </div>"
        "    <!-- Kitty Selection Section -->"
        "    <div id='kittySection' class='section'>"
        "      <h2>Kitty Cards</h2>"
        "      <p id='kittyPrompt'>Click \"Reveal Kitty\" to see the kitty.</p>"
        "      <div id='kittyCards' class='card-row'></div>"
        "      <button class='btn' id='revealKittyButton'>Reveal Kitty</button>"
        "      <button class='btn' id='submitKittyButton' style='display:none;'>Submit Kitty Selection</button>"
        "    </div>"
        "    <!-- Discard Phase -->"
        "    <div id='discardSection' class='section'>"
        "      <h2>Discard Phase</h2>"
        "      <p id='discardMessage'>Select cards to discard (0-4):</p>"
        "      <div id='discardHand' class='card-row'></div>"
        "      <p id='discardCount'>Discarding 0 card(s)</p>"
        "      <button class='btn' id='skipDiscardButton'>Submit Discards</button>"
        "      <p id='computerDiscardInfo'></p>"
        "    </div>"
        "    <!-- Trick Play Section -->"
        "    <div id='trickSection' class='section'>"
        "      <h2>Trick Phase</h2>"
        "      <div id='currentTrick' class='card-row'></div>"
        "      <p id='playPrompt'></p>"
        "      <button class='btn' id='playTrickButton'>Play Selected Card</button>"
        "    </div>"
        "    <!-- Trick Piles / Score -->"
        "    <div id='trickPiles' class='section'>"
        "      <div id='dealerTrickPile'>"
        "        <h3>Dealer's Tricks</h3>"
        "      </div>"
        "      <div id='playerTrickPile'>"
        "        <h3>Your Tricks</h3>"
        "      </div>"
        "    </div>"
        "  </div>"
        "  <footer style='text-align: center; margin-top: 20px;'>&copy; O'Donohue Software</footer>"
        "  <script>"
        "    // --- Utility Functions ---"
        "    async function sendRequest(url, data = {}) {"
        "      try {"
        "        const res = await fetch(url, {"
        "          method: 'POST',"
        "          headers: { 'Content-Type': 'application/json' },"
        "          body: JSON.stringify(data)"
        "        });"
        "        if (!res.ok) {"
        "          const err = await res.json();"
        "          return { error: err.error || 'Error' };"
        "        }"
        "        return await res.json();"
        "      } catch (err) {"
        "        console.error('Network error:', err);"
        "        return { error: err.message };"
        "      }"
        "    }"
        ""
        "    function getCardImageUrl(card) {"
        "      const parts = card.split(' of ');"
        "      if (parts.length !== 2) return '';"
        "      let [rank, suit] = parts;"
        "      // For 10, use '0' so the image URL is correct, e.g. '0H.png'"
        "      let rank_code = rank === '10' ? '0' : (['J','Q','K','A'].includes(rank) ? rank : rank);"
        "      let suit_code = suit[0].toUpperCase();"
        "      return 'https://deckofcardsapi.com/static/img/' + rank_code + suit_code + '.png';"
        "    }"
        ""
        "    function getCardBackUrl() {"
        "      return 'https://deckofcardsapi.com/static/img/back.png';"
        "    }"
        ""
        "    function renderHand(containerId, hand, selectable=false) {"
        "      const container = document.getElementById(containerId);"
        "      container.innerHTML = '';"
        "      hand.forEach(card => {"
        "        const img = document.createElement('img');"
        "        img.src = getCardImageUrl(card);"
        "        img.alt = card;"
        "        img.className = 'card-image';"
        "        if (selectable) {"
        "          img.addEventListener('click', () => {"
        "            if (containerId === 'discardHand') {"
        "              img.classList.toggle('selected-card');"
        "              updateDiscardCount();"
        "            } else {"
        "              // For play selection, only allow one card selected at a time"
        "              [...container.querySelectorAll('.selected-card')].forEach(i => {"
        "                if (i !== img) i.classList.remove('selected-card');"
        "              });"
        "              img.classList.toggle('selected-card');"
        "            }"
        "          });"
        "        }"
        "        container.appendChild(img);"
        "      });"
        "    }"
        ""
        "    function renderKittyCards(containerId, kitty_list) {"
        "      const container = document.getElementById(containerId);"
        "      container.innerHTML = '';"
        "      kitty_list.forEach(card => {"
        "        const img = document.createElement('img');"
        "        img.src = getCardBackUrl();"
        "        img.alt = card;"
        "        img.className = 'card-image';"
        "        img.addEventListener('click', () => {"
        "          img.classList.toggle('selected-card');"
        "        });"
        "        container.appendChild(img);"
        "      });"
        "    }"
        ""
        "    function showSection(id) {"
        "      document.getElementById(id).style.display = 'block';"
        "    }"
        ""
        "    function hideSection(id) {"
        "      document.getElementById(id).style.display = 'none';"
        "    }"
        ""
        "    function updateTrumpDisplay(suit) {"
        "      const suitSymbols = { 'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠' };"
        "      document.getElementById('trumpDisplay').innerHTML = "
        "        `<span>Trump: <span style='font-size:48px;'>${suitSymbols[suit]}</span></span>`;"
        "    }"
        ""
        "    function updateDiscardCount() {"
        "      const count = document.querySelectorAll('#discardHand .selected-card').length;"
        "      document.getElementById('discardCount').innerText = 'Discarding ' + count + ' card(s)';"
        "    }"
        "    // --- End Utility Functions ---"
        ""
        "    // --- Game Initialization ---"
        "    async function initGame() {"
        "      const dealData = await sendRequest('/deal_cards');"
        "      if(dealData.error){"
        "        alert(dealData.error);"
        "        return;"
        "      }"
        "      document.getElementById('dealer').innerText = dealData.dealer;"
        "      renderHand('hand', dealData.player_hand);"
        ""
        "      // Request computer's bid."
        "      const compBidResp = await sendRequest('/computer_first_bid');"
        "      if(compBidResp && !compBidResp.error){"
        "        document.getElementById('computerBid').innerText = 'Computer\\'s bid: ' + compBidResp.computer_bid;"
        "        // Enable only valid bid options based on computer bid."
        "        document.querySelectorAll('.bidButton').forEach(btn => {"
        "          const bidVal = parseInt(btn.getAttribute('data-bid'));"
        "          if(compBidResp.computer_bid == 15){"
        "            btn.disabled = (bidVal !== 0 && bidVal !== 20);"
        "          } else if(compBidResp.computer_bid == 20){"
        "            btn.disabled = (bidVal !== 0 && bidVal !== 25);"
        "          } else if(compBidResp.computer_bid == 25){"
        "            btn.disabled = (bidVal !== 0 && bidVal !== 30);"
        "          } else if(compBidResp.computer_bid == 30){"
        "            // If computer is at 30, you can only pass (0)."
        "            btn.disabled = (bidVal !== 0);"
        "          }"
        "        });"
        "        showSection('biddingSection');"
        "      }"
        "    }"
        "    // --- End Game Initialization ---"
        ""
        "    // --- Bidding Handler ---"
        "    document.querySelectorAll('.bidButton').forEach(btn => {"
        "      btn.addEventListener('click', async () => {"
        "        btn.classList.add('selected-card');"
        "        const bidValue = parseInt(btn.getAttribute('data-bid'));"
        "        const compBidText = document.getElementById('computerBid').innerText;"
        "        const compBid = compBidText ? parseInt(compBidText.replace('Computer\\'s bid: ', '')) : 0;"
        "        const result = await sendRequest('/submit_bid', { player_bid: bidValue, computer_bid: compBid });"
        "        if(result.error){"
        "          document.getElementById('bidError').innerText = result.error;"
        "          return;"
        "        }"
        "        alert('Bid outcome: ' + result.bid_winner);"
        "        hideSection('biddingSection');"
        "        showSection('trumpSelectionSection');"
        "      });"
        "    });"
        "    // --- End Bidding Handler ---"
        ""
        "    // --- Trump Selection Handler ---"
        "    document.querySelectorAll('.trumpButton').forEach(btn => {"
        "      btn.addEventListener('click', async () => {"
        "        const suit = btn.getAttribute('data-suit');"
        "        const resp = await sendRequest('/select_trump', { trump_suit: suit });"
        "        if(resp.error){"
        "          alert(resp.error);"
        "          return;"
        "        }"
        "        updateTrumpDisplay(suit);"
        "        hideSection('trumpSelectionSection');"
        "        renderKittyCards('kittyCards', resp.kitty_cards);"
        "        showSection('kittySection');"
        "      });"
        "    });"
        "    // --- End Trump Selection Handler ---"
        ""
        "    // --- Kitty Selection Handler ---"
        "    document.getElementById('revealKittyButton').addEventListener('click', () => {"
        "      const kittyImgs = document.getElementById('kittyCards').querySelectorAll('img');"
        "      kittyImgs.forEach(img => {"
        "        img.src = getCardImageUrl(img.alt);"
        "      });"
        "      document.getElementById('kittyPrompt').innerText = 'Select the kitty cards you want to add, then click \\'Submit Kitty Selection\\'.';"
        "      document.getElementById('revealKittyButton').style.display = 'none';"
        "      document.getElementById('submitKittyButton').style.display = 'inline-block';"
        "    });"
        "    document.getElementById('submitKittyButton').addEventListener('click', async () => {"
        "      const selected = [...document.querySelectorAll('#kittyCards .selected-card')].map(img => img.alt);"
        "      const resp = await sendRequest('/attach_kitty', { keep_cards: selected });"
        "      if(resp.error){"
        "        alert(resp.error);"
        "        return;"
        "      }"
        "      renderHand('hand', resp.player_hand);"
        "      hideSection('kittySection');"
        "      renderHand('discardHand', resp.player_hand, true);"
        "      showSection('discardSection');"
        "    });"
        "    // --- End Kitty Selection Handler ---"
        ""
        "    // --- Discard Phase Handler ---"
        "    document.getElementById('skipDiscardButton').addEventListener('click', async () => {"
        "      const selected = [...document.querySelectorAll('#discardHand .selected-card')].map(img => img.alt);"
        "      const resp = await sendRequest('/discard_and_draw', { discarded_cards: selected });"
        "      if(resp.error){"
        "        alert(resp.error);"
        "        return;"
        "      }"
        "      renderHand('hand', resp.player_hand);"
        "      hideSection('discardSection');"
        "      showSection('trickSection');"
        "      alert('Trick play phase begins. (Basic trick play logic is used for demonstration.)');"
        "    });"
        "    // --- End Discard Phase Handler ---"
        ""
        "    // --- Trick Play Handler ---"
        "    document.getElementById('playTrickButton').addEventListener('click', async () => {"
        "      const selected = document.querySelector('#hand .selected-card');"
        "      const cardStr = selected ? selected.alt : null;"
        "      const resp = await sendRequest('/play_trick', { played_card: cardStr });"
        "      if(resp.error){"
        "        alert(resp.error);"
        "        return;"
        "      }"
        "      // If the response has a trick_result, display it. If there's hand_scores, game might be done."
        "      alert('Trick result: ' + resp.trick_result + '\\nCurrent Scores: ' + JSON.stringify(resp.hand_scores));"
        "      renderHand('hand', resp.player_hand);"
        "    });"
        "    // --- End Trick Play Handler ---"
        ""
        "    // Initialize the game on page load."
        "    window.addEventListener('load', initGame);"
        "  </script>"
        "</body>"
        "</html>"
    )
    return render_template_string(game_html)

#################################
#           API ROUTES          #
#################################

@app.route("/deal_cards", methods=["POST"])
def api_deal_cards():
    global current_game
    if current_game is None:
        return jsonify({"error": "Game not initialized."}), 400
    current_game.deal_hands()
    dealer = current_game.get_dealer()
    return jsonify({
        "player_hand": current_game.get_player_hand(),
        "dealer": dealer
    })

@app.route("/computer_first_bid", methods=["POST"])
def api_computer_first_bid():
    # For simplicity, just pick a random bid out of these possible
    comp_bid = random.choice([15, 20, 25, 30])
    return jsonify({"computer_bid": comp_bid})

@app.route("/submit_bid", methods=["POST"])
def api_submit_bid():
    data = request.get_json()
    player_bid = data.get("player_bid")
    comp_bid = data.get("computer_bid")

    # If comp is at 30, you can only pass or accept 30. We'll treat pass=0 as losing to computer
    if comp_bid == 30:
        if player_bid == 0:
            # Computer wins automatically
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer"})
        # Otherwise, if you tried to outbid 30, that's invalid
        return jsonify({"error": "Cannot outbid 30 in this simple logic. Pass = 0 only."}), 400

    # If computer passed (0), you must bid exactly 15 or it's invalid
    if comp_bid == 0:
        if player_bid != 15:
            return jsonify({"error": "When opponent passes, you must bid 15."}), 400
        else:
            return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})

    # Standard increment logic: must outbid computer by 5 or pass=0
    let_bid = comp_bid + 5
    if player_bid == 0:
        return jsonify({"computer_bid": comp_bid, "bid_winner": "Computer"})
    elif player_bid != let_bid:
        return jsonify({"error": f"Invalid bid. You must either pass (0) or bid {let_bid}."}), 400
    else:
        return jsonify({"computer_bid": comp_bid, "bid_winner": "Player"})

@app.route("/select_trump", methods=["POST"])
def api_select_trump():
    global current_game
    data = request.get_json()
    suit = data.get("trump_suit", "Hearts")
    kitty = current_game.confirm_trump(suit)
    return jsonify({"kitty_cards": kitty, "trump_suit": suit})

@app.route("/discard_and_draw", methods=["POST"])
def api_discard_and_draw():
    global current_game
    data = request.get_json()
    discards = data.get("discarded_cards", [])
    result = current_game.discard_phase(0, discards)  # Assume human (index 0) is bidder.
    return jsonify(result)

@app.route("/attach_kitty", methods=["POST"])
def api_attach_kitty():
    global current_game
    data = request.get_json()
    keep_cards = data.get("keep_cards", [])
    result = current_game.attach_kitty(0, keep_cards)  # Assume human (index 0) is bidder.
    return jsonify(result)

@app.route("/play_trick", methods=["POST"])
def api_play_trick():
    global current_game
    data = request.get_json()
    played_card = data.get("played_card")
    result_obj, hand_scores = current_game.play_trick(played_card)
    resp = {
        "trick_result": result_obj.get("trick_result", ""),
        "current_trick_cards": result_obj.get("current_trick_cards", {}),
        "trick_winner": result_obj.get("trick_winner", ""),
        "player_hand": current_game.get_player_hand(),
        "hand_scores": hand_scores
    }
    return jsonify(resp)

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    # Run the Flask development server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
