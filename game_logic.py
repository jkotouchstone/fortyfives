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
        # Use a single state variable to manage phases: bidding, trump_selection, discard, trick_play, etc.
        self.phase = "bidding"
        self.kitty = []
        self.current_trick = []

    def deal_hands(self):
        # Reset deck for a new game
        self.deck = Deck()
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)
        self.phase = "bidding"
        self.trump_suit = None
        self.current_bid = None
        self.current_trick = []

    def get_state(self):
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
        rank_code = "0" if card.rank == "10" else card.rank[0]
        suit_code = card.suit[0].upper()
        return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

    def find_card_in_hand(self, hand, card_name):
        return next((c for c in hand if str(c) == card_name), None)

    def process_bid(self, player, bid_val):
        print(f"Received bid from {player}: {bid_val}")
        if self.phase != "bidding":
            return "Bidding is not active."

        if player == "player":
            if bid_val == 0:
                # Player passes; computer wins the bid and will select trump.
                self.phase = "trump_selection"
                self.leading_player = "computer"
                return self.computer_selects_trump()
            elif self.current_bid is None or bid_val > self.current_bid:
                self.current_bid = bid_val
                # Optionally, you could trigger a computer response here.
                return f"You bid {bid_val}. Waiting for computer's response."
            else:
                return "You cannot bid lower than the current bid."
        elif player == "computer":
            if self.current_bid is None or self.current_bid < 20:
                self.current_bid = 20
                self.phase = "discard"
                self.trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
                return f"Computer bids 20 and selects {self.trump_suit} as trump. Moving to discard phase."
            else:
                self.phase = "trump_selection"
                return "Computer passes. You win the bid. Please select a trump suit."

    def computer_selects_trump(self):
        self.trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
        self.phase = "discard"
        return f"Computer wins the bid and selects {self.trump_suit} as trump. Moving to discard phase."

    def discard_cards(self, player, cards_to_discard):
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
        if self.players["computer"]["hand"]:
            card = random.choice(self.players["computer"]["hand"])
            # Call play_card for computer. (Make sure to avoid recursive loops.)
            if self.phase == "trick_play":
                self.play_card("computer", str(card))

    def determine_trick_winner(self):
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

            # If both cards have the same suit, the higher rank wins.
            if player_card.suit == computer_card.suit:
                player_rank = self.get_rank_value(player_card)
                computer_rank = self.get_rank_value(computer_card)
                return "player" if player_rank > computer_rank else "computer"
            else:
                # Default rule for off-suit cards; adjust as needed.
                return "player"
        return "player"

    def get_rank_value(self, card):
        rank_order = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                      "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        return rank_order.get(card.rank, 0)
