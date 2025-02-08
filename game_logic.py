import random

# ---------------------------
# Card and Deck Classes
# ---------------------------
class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # e.g. "♥", "♦", "♣", "♠"
        self.rank = rank  # e.g. "2", "3", …, "10", "J", "Q", "K", "A"

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self):
        return {"suit": self.suit, "rank": self.rank}

class Deck:
    def __init__(self):
        suits = ["♥", "♦", "♣", "♠"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        # (Optional: add a Joker here if desired.)
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards to deal.")
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

# ---------------------------
# Ranking Definitions (Simplified)
# ---------------------------
TRUMP_RANKINGS = {
    "♦": ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "♥": ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "♣": ["5", "J", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"],
    "♠": ["5", "J", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"]
}
OFFSUIT_RANKINGS = {
    "♦": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "♥": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "♣": ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "♠": ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
}

def is_trump(card, trump_suit):
    if card.suit == trump_suit:
        return True
    if card.suit == "♥" and card.rank == "A":
        return True
    return False

def get_trump_value(card, trump_suit):
    ranking = TRUMP_RANKINGS[trump_suit]
    return len(ranking) - ranking.index(card.rank)

def get_offsuit_value(card):
    ranking = OFFSUIT_RANKINGS[card.suit]
    return len(ranking) - ranking.index(card.rank)

# ---------------------------
# Game Class
# ---------------------------
class Game:
    def __init__(self, mode="2p", instructional=False):
        """
        mode: "2p" for heads-up; "3p" for three-way cut-throat.
        instructional: if True, extra help messages may be provided.
        """
        self.mode = mode
        self.instructional = instructional
        self.deck = None
        # Setup players: in 2p, use "player" and "computer";
        # in 3p, use "player", "computer1", and "computer2".
        if self.mode == "2p":
            self.players = {
                "player": {"hand": [], "tricks": [], "score": 0},
                "computer": {"hand": [], "tricks": [], "score": 0}
            }
            self.player_order = ["player", "computer"]
        elif self.mode == "3p":
            self.players = {
                "player": {"hand": [], "tricks": [], "score": 0},
                "computer1": {"hand": [], "tricks": [], "score": 0},
                "computer2": {"hand": [], "tricks": [], "score": 0}
            }
            self.player_order = ["player", "computer1", "computer2"]
        # Set dealer. For 2p, randomly choose; for 3p, start with "player".
        if self.mode == "2p":
            self.dealer = "player" if random.random() < 0.5 else "computer"
        else:
            self.dealer = "player"
        self.kitty = []
        self.trump_suit = None
        self.phase = "bidding"  # phases: bidding, trump, kitty, draw, trick, finished
        self.biddingMessage = ""
        self.currentTrick = []  # List of dicts: {"player": player, "card": card}
        self.trickLog = []     # List of strings summarizing each trick/hand
        self.currentTurn = None  # Whose turn to play in the current trick (from self.player_order)
        self.bidder = None     # Who won the bid ("player", "computer", "computer1", or "computer2")
        self.bid = 0           # The winning bid value
        self.deal_hands()

    def deal_hands(self):
        self.deck = Deck()
        # Deal 5 cards to each player.
        for p in self.players:
            self.players[p]["hand"] = self.deck.deal(5)
        # Deal 3 cards to the kitty.
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.biddingMessage = "Place your bid (15, 20, 25, or 30)."
        self.currentTrick = []
        self.trickLog = []
        # Set the lead for the first trick after bidding.
        # (The winning bidder will choose trump and then lead the first trick.)
        self.currentTurn = None  # Not set until bidding is resolved.
        # In 3p, dealer info is shown in UI; in 2p, a dealer indicator is used.

    def computer_bid(self, computer_id):
        """A simple bidding strategy for a computer player."""
        hand = self.players[computer_id]["hand"]
        has5 = any(card.rank == "5" for card in hand)
        topCount = sum(1 for card in hand if card.rank in ["J", "A", "K"])
        bid = 20 if has5 or topCount >= 2 else (15 if topCount == 1 else 0)
        # Preferred trump is the suit with the most cards.
        suit_counts = {}
        for card in hand:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        best_suit = max(suit_counts, key=suit_counts.get)
        return bid, best_suit

    def process_bid(self, player_bid):
        """In 2p, compare player bid with computer's bid.
           In 3p, simulate bids from both computer players and choose highest.
        """
        if self.mode == "2p":
            comp_bid, comp_trump = self.computer_bid("computer")
            if player_bid >= comp_bid:
                self.bidder = "player"
                self.bid = player_bid
                self.biddingMessage = f"You win the bid ({player_bid} vs {comp_bid}). Please select trump."
                self.phase = "trump"
            else:
                self.bidder = "computer"
                self.bid = comp_bid
                self.trump_suit = comp_trump
                self.biddingMessage = f"Computer wins the bid ({comp_bid} vs {player_bid}). Computer chooses trump."
                self.phase = "kitty"
                # In a real game, computer might also simulate kitty choices.
            # Set the first trick leader to the winning bidder.
            self.currentTurn = self.bidder
        elif self.mode == "3p":
            # Simulate computer bids.
            comp_bid1, comp_trump1 = self.computer_bid("computer1")
            comp_bid2, comp_trump2 = self.computer_bid("computer2")
            # Determine highest bid.
            bids = {"player": player_bid, "computer1": comp_bid1, "computer2": comp_bid2}
            best_bidder = max(bids, key=bids.get)
            best_bid = bids[best_bidder]
            self.bidder = best_bidder
            self.bid = best_bid
            if best_bidder == "player":
                self.biddingMessage = f"You win the bid ({player_bid} vs {comp_bid1} vs {comp_bid2}). Please select trump."
                self.phase = "trump"
            else:
                self.biddingMessage = f"{best_bidder} wins the bid ({best_bid} vs {player_bid}). {best_bidder} chooses trump."
                # For simplicity, if a computer wins, automatically set trump to its preferred suit.
                if best_bidder == "computer1":
                    self.trump_suit = comp_trump1
                else:
                    self.trump_suit = comp_trump2
                self.phase = "kitty"
            self.currentTurn = self.bidder
        return

    def select_trump(self, suit):
        if self.phase == "trump":
            self.trump_suit = suit
            self.phase = "kitty"

    def confirm_kitty(self, keptIndices):
        # Only the winning bidder gets to pick kitty cards.
        if self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            new_hand = [combined[i] for i in keptIndices if i < len(combined)]
            # Enforce at least one card from original hand and no more than 5 cards total.
            if len(new_hand) < 1:
                new_hand = self.players["player"]["hand"][:1]
            if len(new_hand) > 5:
                new_hand = new_hand[:5]
            self.players["player"]["hand"] = new_hand
        # If a computer is the bidder, we won’t simulate its discard here.
        self.phase = "draw"

    def confirm_draw(self):
        # Draw cards for the bidder until they have 5 cards.
        if self.bidder == "player":
            while len(self.players["player"]["hand"]) < 5 and len(self.deck.cards) > 0:
                self.players["player"]["hand"].append(self.deck.deal(1)[0])
        self.phase = "trick"
        # The winning bidder leads the first trick.
        self.currentTurn = self.bidder
        # If the current leader is not the player, auto-play until it's player's turn.
        self.auto_play()

    def next_player(self, current):
        """Return the next player in the circle."""
        idx = self.player_order.index(current)
        next_idx = (idx + 1) % len(self.player_order)
        return self.player_order[next_idx]

    def play_card(self, player, cardIndex):
        """
        Called when a player (human or computer) plays a card.
        For a human move, player == "player" and cardIndex comes from the UI.
        """
        # Validate turn.
        if self.currentTurn != player:
            return  # Not this player's turn.
        # Validate card index.
        if cardIndex < 0 or cardIndex >= len(self.players[player]["hand"]):
            return
        # Remove the card from player's hand and add it to current trick.
        card = self.players[player]["hand"].pop(cardIndex)
        self.currentTrick.append({"player": player, "card": card})
        # Advance turn to the next player.
        self.currentTurn = self.next_player(player)
        # If it's a computer's turn, auto-play.
        self.auto_play()
        # If the trick round is complete, evaluate it.
        if len(self.currentTrick) == len(self.player_order):
            self.finish_trick()
        return

    def auto_play(self):
        """
        Automatically plays cards for computer players until the next turn is the human
        or the trick round is complete.
        """
        while self.currentTurn != "player" and len(self.currentTrick) < len(self.player_order):
            # Current turn is a computer; choose a card automatically.
            available_hand = self.players[self.currentTurn]["hand"]
            if not available_hand:
                break
            # Simple strategy: play a random card.
            cardIndex = random.randrange(len(available_hand))
            self.play_card(self.currentTurn, cardIndex)
            # Note: play_card will update currentTurn and may call auto_play recursively.
        return

    def finish_trick(self):
        """
        When the trick is complete (all players have played), evaluate who won the trick,
        record the trick, and set that player as the leader for the next trick.
        """
        winner = self.evaluate_trick(self.currentTrick)
        trick_result = "Trick: " + ", ".join(f"{p['player']} played {p['card']}" for p in self.currentTrick)
        trick_result += f". Winner: {winner}."
        self.trickLog.append(trick_result)
        # Record the trick for the winner.
        self.players[winner]["tricks"].append(self.currentTrick.copy())
        self.currentTrick = []
        # The winner leads the next trick.
        self.currentTurn = winner
        # If all players have no cards left, complete the hand.
        if all(len(self.players[p]["hand"]) == 0 for p in self.players):
            self.complete_hand()

    def evaluate_trick(self, trick):
        """
        Evaluate the trick and return the winner's player id.
        The rules:
         - The first card's suit is the lead suit.
         - Any trump card beats non-trump cards.
         - Among cards of the same suit, the higher ranked card wins.
         - The Ace of Hearts is always trump.
        """
        if not trick:
            return None
        lead_suit = trick[0]["card"].suit
        # Check if any trump cards were played.
        trump_plays = [p for p in trick if is_trump(p["card"], self.trump_suit)]
        if trump_plays:
            winner_entry = max(trump_plays, key=lambda x: get_trump_value(x["card"], self.trump_suit))
        else:
            # Otherwise, among those that followed suit.
            follow_plays = [p for p in trick if p["card"].suit == lead_suit]
            if follow_plays:
                winner_entry = max(follow_plays, key=lambda x: get_offsuit_value(x["card"]))
            else:
                winner_entry = trick[0]
        return winner_entry["player"]

    def complete_hand(self):
        """
        Called when all players have played all their cards.
        Calculates points for the hand, updates overall scores, and either finishes the game
        or starts a new hand (rotating the dealer).
        """
        # Each trick is worth 5 points.
        points = {p: len(self.players[p]["tricks"]) * 5 for p in self.players}
        # Bonus: last trick gives extra 5 points.
        if self.trickLog:
            if "Winner: " in self.trickLog[-1]:
                last_winner = self.trickLog[-1].split("Winner: ")[-1].strip().strip(".")
                points[last_winner] += 5
        # The winning bidder must meet their bid; if not, they lose that many points.
        if self.bidder in points and points[self.bidder] < self.bid:
            points[self.bidder] = -self.bid
        # Update overall scores.
        for p in self.players:
            self.players[p]["score"] += points[p]
        summary = "Hand over. " + " | ".join(f"{p}: {self.players[p]['score']} pts" for p in self.players)
        self.trickLog.append(summary)
        # Check if any player has reached 120 points.
        if any(self.players[p]["score"] >= 120 for p in self.players):
            self.phase = "finished"
        else:
            self.new_hand()

    def new_hand(self):
        """
        Prepare for a new hand:
         - Rotate the dealer.
         - Clear trick records.
         - Deal new hands.
        """
        # Rotate dealer: move to the next in player_order.
        current_dealer_idx = self.player_order.index(self.dealer)
        next_dealer_idx = (current_dealer_idx + 1) % len(self.player_order)
        self.dealer = self.player_order[next_dealer_idx]
        # For 2p, we want a dealer indicator for the human if they are the dealer.
        self.biddingMessage = "Place your bid (15, 20, 25, or 30)."
        self.deal_hands()
        # In a new hand, the dealer does not automatically win the bid.
        # The bidding phase will determine who becomes the bidder.
        return

    def to_dict(self):
        """
        Return a dictionary representing the current game state.
        This includes:
         - Phase, hands, trick log, scores, current turn, and dealer information.
         - For computer hands, we only return the count.
        """
        state = {
            "gamePhase": self.phase,
            "playerHand": [card.to_dict() for card in self.players["player"]["hand"]],
            "computerHandCount": len(self.players["computer"]["hand"]) if self.mode=="2p" else None,
            "computer1HandCount": len(self.players["computer1"]["hand"]) if self.mode=="3p" else None,
            "computer2HandCount": len(self.players["computer2"]["hand"]) if self.mode=="3p" else None,
            "kitty": [card.to_dict() for card in self.kitty] if self.phase in ["bidding", "kitty"] else [],
            "trumpSuit": self.trump_suit,
            "biddingMessage": self.biddingMessage,
            "currentTrick": [{"player": entry["player"], "card": entry["card"].to_dict()} for entry in self.currentTrick],
            "trickLog": self.trickLog,
            "scoreboard": " | ".join(f"{p}: {self.players[p]['score']}" for p in self.players),
            "currentTurn": self.currentTurn,
            "dealer": self.dealer
        }
        # For kitty/discard/draw phases.
        if self.phase == "kitty" and self.bidder == "player":
            combined = self.players["player"]["hand"] + self.kitty
            state["combinedHand"] = [card.to_dict() for card in combined]
        if self.phase == "draw":
            state["drawHand"] = [card.to_dict() for card in self.players["player"]["hand"]]
        return state
