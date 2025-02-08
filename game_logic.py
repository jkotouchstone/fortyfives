import random

# ---------------------------
# Card and Deck Classes
# ---------------------------

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    def __repr__(self):
        return str(self)

class Deck:
    def __init__(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards to deal.")
        return [self.cards.pop() for _ in range(num_cards)]

# ---------------------------
# Ranking Definitions
# ---------------------------
# Trump ranking orders for each trump suit.
TRUMP_RANKINGS = {
    "Diamonds": ["5", "J", "A♥", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "Hearts":   ["5", "J", "A", "K", "Q", "10", "9", "8", "7", "6", "4", "3", "2"],
    "Clubs":    ["5", "J", "A♥", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"],
    "Spades":   ["5", "J", "A♥", "A", "K", "Q", "2", "3", "4", "6", "7", "8", "9", "10"]
}

# Off-suit ranking orders for cards that are not trump.
OFFSUIT_RANKINGS = {
    "Diamonds": ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "Hearts":   ["K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "A"],
    "Clubs":    ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "Spades":   ["K", "Q", "J", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
}

# ---------------------------
# Helper Functions for Trick Evaluation
# ---------------------------

def is_trump(card, trump_suit):
    """
    A card is trump if its suit matches the trump suit or if it is the Ace of Hearts.
    (Ace of Hearts is always considered part of the trump suit.)
    """
    if card.suit == trump_suit:
        return True
    if card.rank == "A" and card.suit == "Hearts":
        return True
    return False

def get_trump_value(card, trump_suit):
    """
    Return a numeric value for a trump card based on the trump ranking order.
    (Lower index in the ranking means a stronger card; we invert the index so that a higher numeric value is stronger.)
    """
    ranking = TRUMP_RANKINGS[trump_suit]
    # For Ace of Hearts, choose the appropriate token.
    if card.rank == "A" and card.suit == "Hearts":
        token = "A" if trump_suit == "Hearts" else "A♥"
    else:
        token = card.rank
    return len(ranking) - ranking.index(token)

def get_offsuit_value(card):
    """
    Return a numeric value for an off-suit card using the off-suit ranking order.
    Higher value means a stronger card.
    """
    ranking = OFFSUIT_RANKINGS[card.suit]
    return len(ranking) - ranking.index(card.rank)

# ---------------------------
# Game Class with Enhanced AI Logic
# ---------------------------

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = {
            "player": {"hand": [], "score": 0, "tricks": []},
            "computer": {"hand": [], "score": 0, "tricks": []}
        }
        self.dealer = "computer"
        self.trump_suit = None
        self.current_bid = None
        self.phase = "bidding"
        self.kitty = []
        self.current_trick = []  # List of (player, card) tuples
        self.winner = None
        self.seen_cards = []   # For card counting: all cards played so far

        # Placeholder for learning parameters (for future reinforcement learning/CFR extensions)
        self.learning_parameters = {}

    def deal_hands(self):
        """Deals hands to both players and the kitty, and resets game state."""
        self.deck = Deck()
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.trump_suit = None
        self.current_bid = None
        self.current_trick = []
        self.winner = None
        self.seen_cards = []  # Reset seen cards for new game

    def record_trick(self, trick):
        """Record all cards played in a trick for card-counting."""
        for _, card in trick:
            self.seen_cards.append(card)

    def dynamic_trump_value(self, card, trump_suit):
        """
        Adjust the base trump value based on cards already seen.
        (If many high trump cards have been played, a medium trump might win the trick.)
        """
        base_value = get_trump_value(card, trump_suit)
        high_trump_tokens = {"J", "A", "K"}
        played_highs = sum(1 for c in self.seen_cards if is_trump(c, trump_suit) and c.rank in high_trump_tokens)
        adjusted_value = base_value + (played_highs * 0.5)
        return adjusted_value

    def dynamic_offsuit_value(self, card):
        """
        Adjust the off-suit card value based on how many cards of the suit have been seen.
        """
        base_value = get_offsuit_value(card)
        suit = card.suit
        seen_in_suit = sum(1 for c in self.seen_cards if c.suit == suit)
        adjusted_value = base_value + (seen_in_suit * 0.1)
        return adjusted_value

    def evaluate_trick(self, trick):
        """
        Given a trick (a list of (player, card) tuples), determine who wins the trick.
        If any trump cards are played, the highest (dynamically evaluated) trump wins.
        Otherwise, the highest card in the lead suit wins.
        """
        trump = self.trump_suit
        # First, check for trump cards.
        trump_cards = [(player, card) for player, card in trick if is_trump(card, trump)]
        if trump_cards:
            winning_player, winning_card = max(trump_cards, key=lambda x: self.dynamic_trump_value(x[1], trump))
            return winning_player, winning_card
        else:
            # Follow the suit of the first card played (lead suit)
            lead_suit = trick[0][1].suit
            lead_cards = [(player, card) for player, card in trick if card.suit == lead_suit]
            if lead_cards:
                winning_player, winning_card = max(lead_cards, key=lambda x: self.dynamic_offsuit_value(x[1]))
                return winning_player, winning_card
            # Fallback: return the first play (should not occur in legal play)
            return trick[0]

    def evaluate_hand_strength(self, hand, kitty, suit):
        """
        Evaluate the strength of a hand (augmented with kitty cards) if a given suit is chosen as trump.
        A simple heuristic adds bonus points for trump cards, key cards, and suit concentration.
        """
        combined = hand + kitty
        score = 0
        for card in combined:
            # Cards of the target suit or the Ace of Hearts (always trump) add more value.
            if card.suit == suit or (card.rank == "A" and card.suit == "Hearts"):
                score += 2
                if card.rank == "5":
                    score += 3
                if card.rank == "J":
                    score += 2
                if card.rank == "A":
                    score += 2
                if card.rank == "K":
                    score += 1.5
            else:
                score += 0.5  # Some value for off-suit cards
        # Bonus for concentration in the trump suit.
        suit_count = sum(1 for card in combined if card.suit == suit)
        score += suit_count * 0.5
        return score

    def computer_bid(self):
        """
        Evaluate the computer's hand strength (integrated with kitty) to decide on a bid.
        Returns a bid value and a preferred trump suit.
        """
        hand = self.players["computer"]["hand"]
        kitty = self.kitty

        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        suit_strength = {}
        for suit in suits:
            suit_strength[suit] = self.evaluate_hand_strength(hand, kitty, suit)

        best_suit = max(suit_strength, key=suit_strength.get)
        best_score = suit_strength[best_suit]

        # Choose bid based on the best score (thresholds can be tuned)
        if best_score > 20:
            bid_value = 20
        elif best_score > 15:
            bid_value = 15
        else:
            bid_value = 0

        return bid_value, best_suit

    def simulate_trick(self, candidate_card, simulations=500):
        """
        Simulate playing a candidate card from the computer's hand and then simulate
        the opponent's response randomly (with a simple heuristic). Returns the win rate.
        """
        wins = 0
        original_trick = self.current_trick.copy()
        computer_hand_backup = self.players["computer"]["hand"][:]
        opponent_hand_backup = self.players["player"]["hand"][:]

        for _ in range(simulations):
            # Create simulated copies of game state
            sim_trick = original_trick.copy()
            sim_computer_hand = computer_hand_backup[:]
            sim_opponent_hand = opponent_hand_backup[:]

            # Play candidate card
            if candidate_card in sim_computer_hand:
                sim_computer_hand.remove(candidate_card)
            sim_trick.append(("computer", candidate_card))

            # Opponent move: if possible, follow suit with highest off-suit value; otherwise random.
            lead_suit = sim_trick[0][1].suit
            valid_moves = [card for card in sim_opponent_hand if card.suit == lead_suit]
            if valid_moves:
                opponent_card = max(valid_moves, key=get_offsuit_value)
            elif sim_opponent_hand:
                opponent_card = random.choice(sim_opponent_hand)
            else:
                continue

            sim_trick.append(("player", opponent_card))

            # Determine trick winner
            winner, _ = self.evaluate_trick(sim_trick)
            if winner == "computer":
                wins += 1

        return wins / simulations

    def choose_best_move(self):
        """
        For each candidate card in the computer's hand, run Monte Carlo simulations to
        estimate the win rate, and then return the card with the highest expected win rate.
        """
        best_rate = -1
        best_move = None
        for card in self.players["computer"]["hand"]:
            win_rate = self.simulate_trick(card, simulations=500)
            print(f"Simulated win rate for {card}: {win_rate:.2f}")
            if win_rate > best_rate:
                best_rate = win_rate
                best_move = card
        return best_move

    def play_trick(self):
        """
        Play a single trick. The computer uses its Monte Carlo simulation to choose a card.
        The player’s move is simulated (in a full game, you’d replace this with user input).
        """
        self.current_trick = []

        # --- Computer's Move ---
        computer_card = self.choose_best_move()
        print(f"\nComputer plays: {computer_card}")
        self.players["computer"]["hand"].remove(computer_card)
        self.current_trick.append(("computer", computer_card))

        # --- Player's Move (simulated) ---
        player_hand = self.players["player"]["hand"]
        lead_suit = computer_card.suit
        valid_moves = [card for card in player_hand if card.suit == lead_suit]
        if not valid_moves:
            valid_moves = player_hand
        player_card = random.choice(valid_moves)
        print(f"Player plays: {player_card}")
        self.players["player"]["hand"].remove(player_card)
        self.current_trick.append(("player", player_card))

        # Evaluate trick winner.
        winner, winning_card = self.evaluate_trick(self.current_trick)
        print(f"Trick won by {winner} with {winning_card}\n")
        self.record_trick(self.current_trick)
        self.players[winner]["tricks"].append(self.current_trick)
        return winner

    def play_game(self):
        """
        A simple game loop that:
          1. Deals hands and the kitty.
          2. Executes a bidding phase (with computer bidding).
          3. Sets the trump suit.
          4. Plays out tricks until both players’ hands are empty.
          5. Determines and displays the winner.
        """
        self.deal_hands()
        print("=== Hands Dealt ===")
        print("Player hand:", self.players["player"]["hand"])
        print("Computer hand:", self.players["computer"]["hand"])
        print("Kitty:", self.kitty, "\n")
        
        # --- Bidding Phase ---
        comp_bid, comp_trump = self.computer_bid()
        print(f"Computer bids: {comp_bid} with preferred trump: {comp_trump}")
        # For this example, if computer bids > 0, it wins the bid.
        if comp_bid > 0:
            self.trump_suit = comp_trump
            self.winner = "computer"
            print(f"Trump suit set to {self.trump_suit} by computer bidding.\n")
        else:
            # In a complete game, the player could bid; here we default.
            self.trump_suit = comp_trump
            print(f"Trump suit set to {self.trump_suit} (default).\n")
        
        # --- Trick Play Phase ---
        while self.players["player"]["hand"] and self.players["computer"]["hand"]:
            print("=== New Trick ===")
            self.play_trick()
        
        # --- Game Evaluation ---
        comp_trick_count = len(self.players["computer"]["tricks"])
        player_trick_count = len(self.players["player"]["tricks"])
        print("=== Game Over! ===")
        print(f"Computer won {comp_trick_count} tricks.")
        print(f"Player won {player_trick_count} tricks.")
        if comp_trick_count > player_trick_count:
            print("Computer wins the game!")
        elif player_trick_count > comp_trick_count:
            print("Player wins the game!")
        else:
            print("The game is a tie!")

# ---------------------------
# Main Execution
# ---------------------------

if __name__ == "__main__":
    game = Game()
    game.play_game()
