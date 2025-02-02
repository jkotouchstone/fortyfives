import random

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"

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
        self.leading_player = None
        # The game phase can be: "bidding", "trump_selection", "discard", "trick_play", etc.
        self.phase = "bidding"
        self.kitty = []
        self.current_trick = []

    def deal_hands(self):
        """Deals hands to both players and the kitty."""
        self.deck = Deck()  # Reset the deck for a new game
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.trump_suit = None
        self.current_bid = None
        self.current_trick = []

    def get_state(self):
        """Returns the current game state."""
        return {
            "your_cards": [{"name": str(card), "img": self.get_card_image(card)}
                           for card in self.players["player"]["hand"]],
            "computer_count": len(self.players["computer"]["hand"]),
            "kitty_count": len(self.kitty),
            "total_your": self.players["player"]["score"],
            "total_comp": self.players["computer"]["score"],
            "trump_suit": self.trump_suit,
            "dealer": self.dealer,
            "phase": self.phase,
            "card_back": "https://deckofcardsapi.com/static/img/back.png"
        }

    def get_card_image(self, card):
        """Generates the URL for a card's image."""
        rank_code = "0" if card.rank == "10" else card.rank[0]
        suit_code = card.suit[0].upper()
        return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

    def find_card_in_hand(self, hand, card_name):
        """Finds a card in a hand by its string representation."""
        return next((c for c in hand if str(c) == card_name), None)

    def computer_bid(self):
        """
        Evaluates the computer's hand and returns a bid value along with a preferred trump suit.
        It sums the rank values for cards in each suit (using an arbitrary mapping) and picks the
        suit with the highest cumulative value. The strength is then mapped to a bid value.
        """
        hand = self.players["computer"]["hand"]
        rank_order = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                      "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        trump_strength = {}
        for suit in suits:
            trump_strength[suit] = sum(rank_order.get(card.rank, 0) 
                                       for card in hand if card.suit == suit)
        # Choose the suit with the highest strength
        best_suit = max(trump_strength, key=trump_strength.get)
        best_strength = trump_strength[best_suit]

        # Map the strength to a bid value.
        # Adjust these thresholds and bid values as needed.
        if best_strength >= 40:
            bid_value = 30
        elif best_strength >= 35:
            bid_value = 25
        elif best_strength >= 30:
            bid_value = 20
        else:
            bid_value = 0  # Pass if the hand is weak

        return bid_value, best_suit

    def process_bid(self, player, bid_val):
        """
        Processes a bid from the player or computer.
        For the player:
          - If the bid is 0 (pass), the computer's evaluation is used.
          - If the player bids a nonzero value, the computer's bid (based on its hand) is compared.
        Updates the game phase accordingly.
        """
        print(f"Received bid from {player}: {bid_val}")
        if self.phase != "bidding":
            return "Bidding is not active."

        if player == "player":
            if bid_val == 0:
                # Player passes; let the computer evaluate its bid.
                comp_bid, comp_trump = self.computer_bid()
                if comp_bid == 0:
                    # Both players pass; allow player to select trump.
                    self.phase = "trump_selection"
                    return "Both players passed. Please select a trump suit."
                else:
                    self.current_bid = comp_bid
                    self.phase = "discard"
                    self.trump_suit = comp_trump
                    return f"You passed. Computer bids {comp_bid} with {comp_trump} as trump. Moving to discard phase."
            else:
                # Player bids a nonzero value.
                self.current_bid = bid_val
                comp_bid, comp_trump = self.computer_bid()
                if comp_bid > bid_val:
                    self.current_bid = comp_bid
                    self.phase = "discard"
                    self.trump_suit = comp_trump
                    return f"You bid {bid_val}, but computer outbids with {comp_bid} using {comp_trump} as trump. Moving to discard phase."
                else:
                    self.phase = "trump_selection"
                    return f"You win the bid with {bid_val}. Please select a trump suit."
        elif player == "computer":
            # This branch is available if you want to trigger computer bidding explicitly.
            comp_bid, comp_trump = self.computer_bid()
            if comp_bid > (self.current_bid or 0):
                self.current_bid = comp_bid
                self.phase = "discard"
                self.trump_suit = comp_trump
                return f"Computer bids {comp_bid} with {comp_trump} as trump. Moving to discard phase."
            else:
                self.phase = "trump_selection"
                return "Computer passes. You win the bid. Please select a trump suit."

    def set_trump(self, trump):
        """
        Sets the trump suit when the game is in trump_selection phase.
        Validates the trump suit and then updates the game phase to discard.
        """
        if self.phase != "trump_selection":
            return "Not in trump selection phase."
        if trump not in ["Hearts", "Diamonds", "Clubs", "Spades"]:
            return "Invalid trump suit selected."
        self.trump_suit = trump
        self.phase = "discard"
        return f"Trump suit set to {trump}. Moving to discard phase."

    def discard_cards(self, player, cards_to_discard):
        """Handles the discard and draw phase for a player."""
        if self.phase != "discard":
            return {"message": "Discard phase is not active."}

        player_hand = self.players[player]["hand"]
        for card_name in cards_to_discard:
            card = self.find_card_in_hand(player_hand, card_name)
            if card:
                player_hand.remove(card)
            else:
                return {"message": f"Card {card_name} not found in {player}'s hand."}

        new_cards = self.deck.deal(len(cards_to_discard))
        player_hand.extend(new_cards)

        # When both players have 5 cards, move to trick play.
        if len(self.players["player"]["hand"]) == 5 and len(self.players["computer"]["hand"]) == 5:
            self.phase = "trick_play"

        return {"message": f"{player.capitalize()} discarded and drew {len(cards_to_discard)} cards."}

    def play_card(self, player, card_name):
        """Handles playing a card during a trick."""
        if self.phase != "trick_play":
            return {"message": "Trick play is not active."}

        player_hand = self.players[player]["hand"]
        card = self.find_card_in_hand(player_hand, card_name)
        if not card:
            return {"message": "Invalid card."}

        player_hand.remove(card)
        self.current_trick.append({"player": player, "card": card})
        msg = f"{player.capitalize()} played {card}."

        if len(self.current_trick) == 1 and player == "player":
            # Simulate the computer's move after the player plays.
            self.computer_play_card()

        if len(self.current_trick) == 2:
            winner = self.determine_trick_winner()
            self.players[winner]["tricks"].append(self.current_trick)
            self.current_trick = []
            msg += f" {winner.capitalize()} wins the trick."

        return {"message": msg}

    def computer_play_card(self):
        """Simulates the computer playing a card."""
        if self.players["computer"]["hand"]:
            card = random.choice(self.players["computer"]["hand"])
            if self.phase == "trick_play":
                self.play_card("computer", str(card))

    def determine_trick_winner(self):
        """Determines the winner of the current trick."""
        player_entry = next((entry for entry in self.current_trick if entry["player"] == "player"), None)
        computer_entry = next((entry for entry in self.current_trick if entry["player"] == "computer"), None)

        if player_entry and computer_entry:
            player_card = player_entry["card"]
            computer_card = computer_entry["card"]

            # Check if trump was played.
            if player_card.suit == self.trump_suit and computer_card.suit != self.trump_suit:
                return "player"
            if computer_card.suit == self.trump_suit and player_card.suit != self.trump_suit:
                return "computer"

            # If both cards are the same suit, the higher rank wins.
            if player_card.suit == computer_card.suit:
                player_rank = self.get_rank_value(player_card)
                computer_rank = self.get_rank_value(computer_card)
                return "player" if player_rank > computer_rank else "computer"
            else:
                # Default rule for off-suit cards (adjust as needed).
                return "player"
        return "player"

    def get_rank_value(self, card):
        """Returns the rank value of a card."""
        rank_order = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                      "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        return rank_order.get(card.rank, 0)
