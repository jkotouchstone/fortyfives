import os
import random
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

#################################
#       GLOBAL GAME STATE       #
#################################

current_game = None

#################################
#         GAME CLASSES          #
#################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        # For 45's we use a smaller, nonstandard deck of certain ranks:
        ranks = ["2", "3", "4", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        for s in suits:
            for r in ranks:
                self.cards.append(Card(s, r))
        # Ensure special 5 of Hearts is included
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
        self.hand = []
        self.score = 0
        self.tricks_won = 0

    def set_hand(self, cards):
        self.hand = cards

    def add_to_hand(self, cards):
        self.hand.extend(cards)

    def get_hand_strings(self):
        return [str(card) for card in self.hand]

class Game:
    def __init__(self):
        # Two players: (index 0) = "You", (index 1) = "Computer"
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.leading_player = 0  # Let's default the lead to the human
        self.trick_count = 0
        self.trick_history = []
        self.trick_log_text = ""
        # Store starting scores so we can track how many points earned each hand
        self.starting_scores = {p.name: p.score for p in self.players}

    def deal_hands(self):
        self.deck.shuffle()
        self.kitty = self.deck.deal(3)
        for p in self.players:
            p.set_hand([])
            p.tricks_won = 0
        for p in self.players:
            p.add_to_hand(self.deck.deal(5))
        self.trick_count = 0
        self.trick_history = []
        self.trick_log_text = ""
        self.starting_scores = {p.name: p.score for p in self.players}
        self.trump_suit = None

    def get_player_hand(self):
        return self.players[0].get_hand_strings()

    def get_dealer(self):
        # Hard-code "You" as the dealer in this example
        return self.players[0].name

    def confirm_trump(self, suit):
        self.trump_suit = suit
        return [str(card) for card in self.kitty]

    def discard_phase(self, bidder_index, discards):
        bidder = self.players[bidder_index]
        initial_count = len(bidder.hand)
        bidder.hand = [c for c in bidder.hand if str(c) not in discards]
        discarded = initial_count - len(bidder.hand)
        missing = 5 - len(bidder.hand)
        if missing > 0:
            bidder.add_to_hand(self.deck.draw(missing))
        return {
            "player_hand": self.players[0].get_hand_strings(),
            "discard_count": discarded
        }

    def attach_kitty(self, player_index, keep_list):
        bidder = self.players[player_index]
        for card_str in keep_list:
            for c in self.kitty:
                if str(c) == card_str:
                    bidder.add_to_hand([c])
        self.kitty = [c for c in self.kitty if str(c) not in keep_list]
        if len(bidder.hand) > 5:
            bidder.hand = bidder.hand[:5]
        return {"player_hand": self.players[0].get_hand_strings()}

    def play_trick(self, played_card=None):
        """ Very naive 'trick' logic just for demonstration. """
        played = {}
        if self.leading_player == 1:  # Computer leads
            # If no computer card, no trick
            if not self.players[1].hand:
                return {"trick_result": "Computer has no cards left."}, None
            comp_card = self.players[1].hand.pop(0)
            played[1] = comp_card
            self.trick_log_text = f"Computer led with {comp_card}."
            if played_card:
                # Validate your card
                if played_card not in self.get_player_hand():
                    return {"trick_result": "Invalid card."}, None
                your_card = next(c for c in self.players[0].hand if str(c) == played_card)
                self.players[0].hand.remove(your_card)
                played[0] = your_card
                self.trick_log_text += f" You played {your_card}."
        else:  # Human leads
            if not played_card:
                return {"trick_result": "You must select a card to lead."}, None
            if played_card not in self.get_player_hand():
                return {"trick_result": "Invalid card."}, None
            your_card = next(c for c in self.players[0].hand if str(c) == played_card)
            self.players[0].hand.remove(your_card)
            played[0] = your_card
            self.trick_log_text = f"You led {your_card}."
            # Computer plays
            if self.players[1].hand:
                comp_card = self.players[1].hand.pop(0)
                played[1] = comp_card
                self.trick_log_text += f" Computer played {comp_card}."

        # Determine winner (extremely simplified: string compare)
        if not played.get(1):
            winner = "You"
        elif not played.get(0):
            winner = "Computer"
        else:
            winner = "You" if str(played[0]) > str(played[1]) else "Computer"
        # Award trick
        if winner == "You":
            self.players[0].score += 5
            self.players[0].tricks_won += 1
            self.leading_player = 0
        else:
            self.players[1].score += 5
            self.players[1].tricks_won += 1
            self.leading_player = 1

        self.trick_count += 1
        current_trick = {
            "You": str(played.get(0, "")),
            "Computer": str(played.get(1, ""))
        }
        self.trick_history.append({
            "trick_number": self.trick_count,
            "cards": current_trick,
            "winner": winner
        })

        # If 5 tricks or no cards left in your hand, hand is done
        if self.trick_count >= 5 or len(self.players[0].hand) == 0:
            # Calculate how many points each player earned in this hand
            hand_scores = {
                p.name: p.score - self.starting_scores[p.name]
                for p in self.players
            }
            full_result = self.trick_log_text + f" Trick winner: {winner}. Hand complete."
            return {"trick_result": full_result}, hand_scores
        else:
            return {
                "trick_result": self.trick_log_text,
                "winner": winner
            }, None

#################################
#          ROUTES/API           #
#################################

@app.route("/")
def landing():
    global current_game
    current_game = Game()
    current_game.deal_hands()
    dealer = current_game.get_dealer()

    page_html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>45's Heads Up</title>
      </head>
      <body style="background-color: #35654d; color: #fff; font-family: Arial, sans-serif; text-align: center;">
        <div id="gameContainer" style="margin: 50px auto; width: 800px; background-color: #2e4e41; padding: 20px; border-radius: 10px;">
          <h1>45's Heads Up</h1>
          <p>Dealer: {dealer}</p>
          <h3>Your Hand:</h3>
          <div id="handContainer" style="margin-bottom: 20px;"></div>
          <button onclick="dealAgain()">Deal Again</button>
          <hr>
          <div id="gameActions"></div>
        </div>

        <script>
          // A quick utility to do POSTs with JSON
          async function postJSON(url, data) {{
            const resp = await fetch(url, {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify(data || {{}})
            }});
            return resp.json();
          }}

          // Renders your hand
          function renderHand(cards) {{
            const container = document.getElementById('handContainer');
            container.innerHTML = '';
            cards.forEach(card => {{
              const div = document.createElement('div');
              div.style.display = 'inline-block';
              div.style.margin = '5px';
              div.style.padding = '5px';
              div.style.border = '1px solid #fff';
              div.innerText = card;
              container.appendChild(div);
            }});
          }}

          // Refresh hand from server
          async function refreshHand() {{
            // We can call an endpoint to see what's in hand. But we already have the info on initial load in this example.
            const result = await postJSON('/deal_cards');
            if (result.error) {{
              alert('Error: ' + result.error);
            }} else {{
              renderHand(result.player_hand);
            }}
          }}

          // Start the game by showing player's hand
          window.addEventListener('DOMContentLoaded', (event) => {{
            // We could do a quick fetch to get the player's hand from server
            // But the server is dealing on the landing() route
            // Let's call the same endpoint to get the initial data
            postJSON('/deal_cards').then(result => {{
              if (!result.error) {{
                renderHand(result.player_hand);
              }} else {{
                alert(result.error);
              }}
            }});
          }});

          // Simple button to re-deal
          async function dealAgain() {{
            const result = await postJSON('/deal_cards');
            if (!result.error) {{
              renderHand(result.player_hand);
            }} else {{
              alert(result.error);
            }}
          }}
        </script>
      </body>
    </html>
    """
    return render_template_string(page_html)

@app.route("/deal_cards", methods=["POST"])
def deal_cards():
    global current_game
    if not current_game:
        current_game = Game()
    current_game.deal_hands()
    return jsonify({
        "player_hand": current_game.get_player_hand(),
        "dealer": current_game.get_dealer()
    })

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

# If you want to run locally: "python app.py"
# On Render, you often set "Start Command" to "gunicorn app:app"
if __name__ == "__main__":
    # For local dev:
    #   python app.py
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
