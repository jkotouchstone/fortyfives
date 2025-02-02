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
        return [self.cards.pop() for _ in range(num_cards)]

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = {
            "player": {"hand": [], "score": 0, "tricks": []},
            "computer": {"hand": [], "score": 0, "tricks": []}
        }
        self.dealer = "computer"
        self.current_bid = None
        self.leading_player = None
        self.trump_suit = None
        self.bidding_active = True
        self.trick_play_active = False
        self.kitty = []
        self.current_trick = []

    def deal_hands(self):
        self.players["player"]["hand"] = self.deck.deal(5)
        self.players["computer"]["hand"] = self.deck.deal(5)
        self.kitty = self.deck.deal(3)

    def get_state(self):
    state = {
        "your_cards": [{"name": str(card), "img": self.get_card_image(card)} for card in self.players["player"]["hand"]],
        "computer_count": len(self.players["computer"]["hand"]),
        "kitty_count": len(self.kitty),
        "total_your": self.players["player"]["score"],
        "total_comp": self.players["computer"]["score"],
        "trump_suit": self.trump_suit,
        "leading_player": self.leading_player,
        "bidding_active": self.bidding_active,
        "trick_play_active": self.trick_play_active,
        "card_back": "https://deckofcardsapi.com/static/img/back.png"
    }

    # Log the state to the console
    print("DEBUG: Game State:", state)
    return state

    def get_card_image(self, card):
        rank_code = "0" if card.rank == "10" else card.rank[0]
        suit_code = card.suit[0].upper()
        return f"https://deckofcardsapi.com/static/img/{rank_code}{suit_code}.png"

    def is_bidding_active(self):
        return self.bidding_active

    def process_bid(self, player, bid_val):
        if self.bidding_active:
            if player == "player":
                if bid_val == 0:
                    self.bidding_active = False
                    self.leading_player = "computer"
                    self.computer_selects_trump()
                    return "You passed. Computer wins the bid."
                else:
                    self.current_bid = bid_val
                    self.leading_player = "player"
                    return f"You bid {bid_val}. Waiting for computer's response."
            elif player == "computer":
                if bid_val <= 20:
                    self.bidding_active = False
                    self.leading_player = "computer"
                    self.computer_selects_trump()
                    return f"Computer bids {bid_val} and wins the bid."
                else:
                    self.bidding_active = False
                    return "Computer passes. You win the bid."
        return "Bidding phase has ended."

    def computer_selects_trump(self):
        self.trump_suit = random.choice(["Hearts", "Diamonds", "Clubs", "Spades"])
        print(f"Computer selected {self.trump_suit} as trump.")

    def is_card_play_allowed(self):
        return not self.bidding_active and self.trick_play_active

    def play_card(self, player, card_name):
        if not self.trick_play_active:
            return {"message": "Trick play is not active."}

        player_hand = self.players[player]["hand"]
        card = next((c for c in player_hand if str(c) == card_name), None)
        if not card:
            return {"message": "Invalid card."}

        player_hand.remove(card)
        self.current_trick.append({"player": player, "card": card})

        if len(self.current_trick) == 2:
            winner = self.determine_trick_winner()
            self.players[winner]["tricks"].append(self.current_trick)
            self.current_trick = []
            return {"message": f"{winner.capitalize()} wins the trick."}
        else:
            return {"message": f"{player.capitalize()} played {card}."}

    def determine_trick_winner(self):
        player_card = next((entry for entry in self.current_trick if entry["player"] == "player"), None)
        computer_card = next((entry for entry in self.current_trick if entry["player"] == "computer"), None)

        if player_card and computer_card:
            player_rank = self.get_rank_value(player_card["card"])
            computer_rank = self.get_rank_value(computer_card["card"])

            if player_card["card"].suit == self.trump_suit and computer_card["card"].suit != self.trump_suit:
                return "player"
            if computer_card["card"].suit == self.trump_suit and player_card["card"].suit != self.trump_suit:
                return "computer"

            return "player" if player_rank > computer_rank else "computer"

        return "player"

    def get_rank_value(self, card):
        rank_order = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                      "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        return rank_order.get(card.rank, 0)
