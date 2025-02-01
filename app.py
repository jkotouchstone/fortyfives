import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

###############################################################################
#                                  RANK TABLES                                #
###############################################################################
# These dictionaries store the rank of each card under different trump/off-suit
# scenarios, following Forty-Fives rules. The highest integer => the strongest card.

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
    # For black trump suits, "red is high, black is low" is partially overridden by the unique 45's order.
    # We'll treat 2-4 as higher than 6-10, based on common references. Adjust as needed for exact local rules.
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
    # K♦ Q♦ J♦ 10♦ 9♦ 8♦ 7♦ 6♦ 5♦ 4♦ 3♦ 2♦ A♦ (A♦ is weakest off-suit diamond)
    "K of Diamonds": 200, "Q of Diamonds": 199, "J of Diamonds": 198, "10 of Diamonds": 197,
    "9 of Diamonds": 196, "8 of Diamonds": 195, "7 of Diamonds": 194, "6 of Diamonds": 193,
    "5 of Diamonds": 192, "4 of Diamonds": 191, "3 of Diamonds": 190, "2 of Diamonds": 189,
    "A of Diamonds": 188
}
OFFSUIT_HEARTS = {
    # K♥ Q♥ J♥ 10♥ 9♥ 8♥ 7♥ 6♥ 5♥ 4♥ 3♥ 2♥
    # A♥ is never off-suit, it's always trump, so we omit "A of Hearts" from here.
    "K of Hearts": 200, "Q of Hearts": 199, "J of Hearts": 198, "10 of Hearts": 197,
    "9 of Hearts": 196, "8 of Hearts": 195, "7 of Hearts": 194, "6 of Hearts": 193,
    "5 of Hearts": 192, "4 of Hearts": 191, "3 of Hearts": 190, "2 of Hearts": 189
}
OFFSUIT_CLUBS = {
    # K♣ Q♣ J♣ A♣ 2♣ 3♣ 4♣ 5♣ 6♣ 7♣ 8♣ 9♣ 10♣
    # "red is high, black is low" => 2 is quite high among the black suits, but face cards outrank it.
    "K of Clubs": 200, "Q of Clubs": 199, "J of Clubs": 198, "A of Clubs": 197,
    "2 of Clubs": 196, "3 of Clubs": 195, "4 of Clubs": 194, "5 of Clubs": 193,
    "6 of Clubs": 192, "7 of Clubs": 191, "8 of Clubs": 190, "9 of Clubs": 189,
    "10 of Clubs": 188
}
OFFSUIT_SPADES = {
    # K♠ Q♠ J♠ A♠ 2♠ 3♠ 4♠ 5♠ 6♠ 7♠ 8♠ 9♠ 10♠
    "K of Spades": 200, "Q of Spades": 199, "J of Spades": 198, "A of Spades": 197,
    "2 of Spades": 196, "3 of Spades": 195, "4 of Spades": 194, "5 of Spades": 193,
    "6 of Spades": 192, "7 of Spades": 191, "8 of Spades": 190, "9 of Spades": 189,
    "10 of Spades": 188
}

def get_card_rank(card_str: str, trump_suit: str) -> int:
    """
    Return an integer rank for card_str (e.g. "5 of Hearts") under the given trump suit.
    A♥ is included in each trump dictionary. If the card is not in the trump dictionary,
    it's off-suit, so we look up the off-suit dictionary for that suit.
    """
    # Quick map from "Hearts"/"Diamonds"/"Clubs"/"Spades" to the relevant dictionary
    # if trump is that suit.
    # Then if card doesn't appear in that dictionary, we look up off-suit dicts.
    if trump_suit == "Diamonds":
        if card_str in TRUMP_DIAMONDS:
            return TRUMP_DIAMONDS[card_str]
        else:
            # off-suit
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
            # off-suit
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
            # off-suit
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
            # off-suit
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
#                                GAME CLASSES                                 #
###############################################################################

class Card:
    def __init__(self, suit, rank):
        self.suit = suit       # e.g. "Hearts"
        self.rank = rank       # e.g. "5"
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = []
        for s in suits:
            for r in ranks:
                self.cards.append(Card(s, r))
        self.shuffle()
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def deal(self, num_cards):
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0  # up to 120
        self.tricks_won = 0  # per round
    
    def add_to_hand(self, cards):
        self.hand.extend(cards)
    
    def __repr__(self):
        return f"Player({self.name}, score={self.score}, hand={[str(c) for c in self.hand]})"

###############################################################################
#                                MAIN GAME LOGIC                              #
###############################################################################

class Game:
    def __init__(self):
        self.players = [Player("You"), Player("Computer")]
        self.deck = Deck()
        self.kitty = []
        self.trump_suit = None
        self.bid_winner = None  # index 0 or 1
        self.bid = 0            # 15, 20, 25, or 30
        self.leading_player = 0
        self.highest_card_played = None
        self.highest_card_owner = None

    def reset_round_state(self):
        """ Clear round-related state without resetting cumulative scores. """
        self.deck = Deck()
        self.kitty.clear()
        self.trump_suit = None
        self.bid_winner = None
        self.bid = 0
        self.leading_player = 0
        self.highest_card_played = None
        self.highest_card_owner = None
        for p in self.players:
            p.hand.clear()
            p.tricks_won = 0

    def deal_hands(self, dealer_index=1):
        """
        Deal 3 cards each, then 3 to kitty, then 2 cards each, in heads-up order:
        Eldest hand (left of dealer) first, then dealer.
        For heads-up, if dealer_index=1, that means player 0 is eldest hand.
        """
        self.deck.shuffle()
        # Clear old
        for p in self.players:
            p.hand.clear()
        self.kitty.clear()

        # If dealer is 1, eldest is 0
        eldest_index = 0 if dealer_index == 1 else 1

        # 3 cards each
        self.players[eldest_index].add_to_hand(self.deck.deal(3))
        self.players[dealer_index].add_to_hand(self.deck.deal(3))

        # 3 to kitty
        self.kitty.extend(self.deck.deal(3))

        # 2 each
        self.players[eldest_index].add_to_hand(self.deck.deal(2))
        self.players[dealer_index].add_to_hand(self.deck.deal(2))

    def get_player_hand_strings(self, player_index=0):
        return [str(c) for c in self.players[player_index].hand]

    def perform_bidding(self, dealer_index=1, player_bid=0):
        """
        1) Player 0 (eldest) might pass (0) or pick [15,20,25,30].
        2) Player 1 (dealer) might also do so.
        3) If both pass, dealer is "bagged" at 15.
        """
        # We'll do a naive computer bid:
        comp_bid = random.choice([0, 15, 20, 25, 30])

        # eldest is 0 if dealer=1, else 1
        eldest_index = 0 if dealer_index == 1 else 1
        dealer_bid = None

        if eldest_index == 0:
            # That means player 0 is the first bidder (the "human" in this example).
            # We have player's bid in player_bid param
            # Then computer (player 1) as second bidder.
            dealer_bid = comp_bid
            p0_bid = player_bid
            p1_bid = dealer_bid
        else:
            # If we had more logic for if the user is the dealer, we'd do that
            # But let's keep it consistent for a single scenario.
            p0_bid = comp_bid
            p1_bid = player_bid
        
        # If both pass => dealer forced to 15
        if p0_bid == 0 and p1_bid == 0:
            if dealer_index == 1:
                p1_bid = 15
            else:
                p0_bid = 15
        
        # Determine winner
        if p0_bid > p1_bid:
            self.bid_winner = 0
            self.bid = p0_bid
        else:
            self.bid_winner = 1
            self.bid = p1_bid

    def set_trump_suit(self, suit):
        """ Called by the bid winner to pick trump. Must have at least 1 card in that suit or A♥. """
        self.trump_suit = suit

    def attach_kitty(self):
        """
        Bidder takes the kitty. Then discards down to 5 if they have more.
        Simple discard logic: keep all trump + A♥, discard everything else first.
        """
        bidder = self.players[self.bid_winner]
        # Add kitty
        bidder.hand.extend(self.kitty)
        self.kitty.clear()

        # Discard logic
        def is_trump_or_ace_hearts(c):
            if c.suit == self.trump_suit:
                return True
            if c.suit == "Hearts" and c.rank == "A":
                return True
            return False

        # Sort bidder's hand so that trump & A♥ are first
        bidder.hand.sort(
            key=lambda card: (is_trump_or_ace_hearts(card), get_card_rank(str(card), self.trump_suit)),
            reverse=True
        )

        # Discard from the end if we have more than 5
        while len(bidder.hand) > 5:
            bidder.hand.pop()

    def allow_other_player_discard(self):
        """
        If the other player also discards (optional rule).
        We'll do a naive approach: auto-discard off-suit, keep up to 5.
        Then draw from deck.
        """
        for i, p in enumerate(self.players):
            if i == self.bid_winner:
                continue
            # simple logic: keep only trump + A♥, discard everything else
            p.hand.sort(
                key=lambda card: get_card_rank(str(card), self.trump_suit),
                reverse=True
            )
            # We keep up to 5. But if some players want to keep an off-suit card, they'd need advanced logic.
            while len(p.hand) > 5:
                p.hand.pop()

            # Draw if we have fewer than 5, from top of deck
            while len(p.hand) < 5 and len(self.deck.cards) > 0:
                p.hand.append(self.deck.deal(1)[0])

    def play_trick(self, lead_card_str=None):
        """
        The leading player places a card. Then the other player responds.
        We handle:
         - Must follow suit if possible (unless you only have 5, J, or A♥ in that suit).
         - If trump is led, must follow trump unless you only have big 3 left.
         - Determine winner based on get_card_rank(...).
         - Add 5 points to winner, track if card is highest so far.

        For a single call, we assume it either leads or follows based on a state machine in the front-end.
        This function can be called multiple times: one call for the lead, one for the follow.
        
        However, to keep it simpler in a demonstration, we'll do a "single function call plays the entire trick"
        with an optional 'lead_card_str' from the user. The computer then picks its card automatically.
        We return the result.
        """
        # If no lead_card_str provided (meaning it's the computer's lead?), let's pick a lead from the computer
        if lead_card_str is None and self.leading_player == 1:
            # Computer leads
            lead_card_str = self.computer_select_lead_card(self.players[1].hand)
            # remove from hand
            lead_card = next(c for c in self.players[1].hand if str(c) == lead_card_str)
            self.players[1].hand.remove(lead_card)
            lead_suit = lead_card.suit
            trick_log = f"Computer led {lead_card_str}. "

            # Now user responds if possible
            respond_card_str = self.user_follow_card(lead_suit)
            if not respond_card_str:
                return {"error": "No valid follow from user."}
            respond_card = next(c for c in self.players[0].hand if str(c) == respond_card_str)
            self.players[0].hand.remove(respond_card)
            trick_log += f"You played {respond_card_str}. "

            # Evaluate winner
            winner_index = self.evaluate_trick_winner([ (1, lead_card), (0, respond_card) ])
            # Add 5 points
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            trick_log += f"Winner: {self.players[winner_index].name}."

            # Track highest card
            for (pid, card) in [(1, lead_card), (0, respond_card)]:
                rank_val = get_card_rank(str(card), self.trump_suit)
                if self.highest_card_played is None or rank_val > get_card_rank(self.highest_card_played, self.trump_suit):
                    self.highest_card_played = str(card)
                    self.highest_card_owner = pid

            self.leading_player = winner_index
            return {"trick_result": trick_log, "player_hand": self.get_player_hand_strings(0)}

        elif self.leading_player == 0:
            # User leads
            if lead_card_str not in [str(c) for c in self.players[0].hand]:
                return {"error": "User tried to lead a card not in hand."}
            lead_card = next(c for c in self.players[0].hand if str(c) == lead_card_str)
            self.players[0].hand.remove(lead_card)
            lead_suit = lead_card.suit
            trick_log = f"You led {lead_card_str}. "

            # Computer responds
            respond_card_str = self.computer_follow_card(self.players[1], lead_suit)
            respond_card = next(c for c in self.players[1].hand if str(c) == respond_card_str)
            self.players[1].hand.remove(respond_card)
            trick_log += f"Computer played {respond_card_str}. "

            # Evaluate winner
            winner_index = self.evaluate_trick_winner([ (0, lead_card), (1, respond_card) ])
            self.players[winner_index].score += 5
            self.players[winner_index].tricks_won += 1
            trick_log += f"Winner: {self.players[winner_index].name}."

            # Track highest card
            for (pid, card) in [(0, lead_card), (1, respond_card)]:
                rank_val = get_card_rank(str(card), self.trump_suit)
                if self.highest_card_played is None or rank_val > get_card_rank(self.highest_card_played, self.trump_suit):
                    self.highest_card_played = str(card)
                    self.highest_card_owner = pid

            self.leading_player = winner_index
            return {"trick_result": trick_log, "player_hand": self.get_player_hand_strings(0)}
        else:
            return {"error": "Expected lead_card_str for user lead or none if computer leads."}

    def evaluate_trick_winner(self, played_cards):
        """
        played_cards: list of tuples (player_index, card_obj)
        The first item in played_cards is the lead card. If a trump is played by anyone, highest trump wins.
        Otherwise, highest in the lead suit wins.
        """
        lead_suit = played_cards[0][1].suit  # suit of the first card
        # check if any trumps
        trump_cards = []
        for (pid, c) in played_cards:
            if get_card_rank(str(c), self.trump_suit) >= 100:
                trump_cards.append((pid, c))
        if trump_cards:
            # highest trump among trump_cards
            winner_pid, winner_card = max(trump_cards, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
            return winner_pid
        else:
            # no trump played => highest in lead suit
            lead_suit_cards = [(pid, c) for (pid, c) in played_cards if c.suit == lead_suit]
            winner_pid, winner_card = max(lead_suit_cards, key=lambda x: get_card_rank(str(x[1]), self.trump_suit))
            return winner_pid

    ############# Simple "AI" logic for demonstration #############
    def computer_choose_bid(self):
        # Very naive: pick from [0,15,20,25,30]
        return random.choice([0, 15, 20, 25, 30])

    def computer_pick_trump_suit(self):
        # Also naive: pick a random suit from among cards in hand
        comp_hand = self.players[1].hand
        suits_in_hand = set([c.suit for c in comp_hand])
        # If hearts is not in suits_in_hand but the comp has A♥, that can count as hearts
        # but let's keep it simpler
        if len(suits_in_hand) == 0:
            return "Hearts"
        return random.choice(list(suits_in_hand))

    def computer_select_lead_card(self, comp_hand):
        # naive: just pick the highest card in hand (by rank)
        comp_hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
        return str(comp_hand[0])

    def computer_follow_card(self, player_obj, lead_suit):
        # must follow suit if possible unless the only suit cards are big 3
        valid_cards = []
        big_three_strs = [f"5 of {self.trump_suit}", f"J of {self.trump_suit}", "A of Hearts"]
        for c in player_obj.hand:
            if c.suit == lead_suit:
                # This is a normal follow
                valid_cards.append(c)
        if valid_cards:
            # play the lowest or highest? Let's do highest
            valid_cards.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
            return str(valid_cards[0])
        else:
            # no normal suit -> can play trump or slough
            # but must play trump if has it, unless only big 3 remain
            trump_cards = [c for c in player_obj.hand if get_card_rank(str(c), self.trump_suit) >= 100]
            # Check for big3
            non_big3_trump = [c for c in trump_cards if str(c) not in big_three_strs]
            if non_big3_trump:
                # play highest or lowest? We'll pick highest
                non_big3_trump.sort(key=lambda c: get_card_rank(str(c), self.trump_suit), reverse=True)
                return str(non_big3_trump[0])
            else:
                # either no trump or only big3 => slough anything
                # pick the lowest card overall
                player_obj.hand.sort(key=lambda c: get_card_rank(str(c), self.trump_suit))
                return str(player_obj.hand[0])

    def user_follow_card(self, lead_suit):
        # This is where the *front-end* would normally pick a card from the user.
        # In a console game, you'd ask input. In a web game, you'd rely on a route.
        # Here, let's just say we can't auto-play the user's card without a front-end choice.
        return None  # we can't continue without user input

    ##########################################################

    def finalize_hand(self):
        """
        After 5 tricks, add the bonus +5 to the highest card owner,
        then apply bid logic (bidder must meet or exceed their points or lose the bid).
        Return a dict summarizing the results.
        """
        # Bonus trick
        if self.highest_card_owner is not None:
            self.players[self.highest_card_owner].score += 5

        # Tally how many points each player got THIS round
        # Each trick = 5 points, bonus card holder got an extra +5
        # We can figure it out by comparing pre-round and post-round, or we can track trick points directly.
        # For demonstration, let's do the difference between new score and old round start, etc.
        # (We haven't stored old scores, so let's do a simpler approach: each player's trick_won * 5, plus maybe the bonus.)

        bidder = self.players[self.bid_winner]
        non_bidder_idx = 1 - self.bid_winner
        bidder_points_this_round = bidder.tricks_won * 5
        if self.highest_card_owner == self.bid_winner:
            bidder_points_this_round += 5  # bonus

        # Did bidder meet the bid?
        if bidder_points_this_round >= self.bid:
            # They keep what they earned
            pass
        else:
            # They lose their bid
            bidder.score -= self.bid

        # The other player's round points:
        other_tricks = self.players[non_bidder_idx].tricks_won * 5
        if self.highest_card_owner == non_bidder_idx:
            other_tricks += 5
        # We already added the trick points to their self.score along the way. In this simple approach,
        # we are adding 5 each time they won a trick. So at this point, they already have those points in self.score.
        # If we want to use the "score" as final, we can skip re-adding them. We just have to ensure the final score is correct.

        # However, we do need to adjust if the bidder was "set," because we subtracted their bid from bidder.score above
        # That doesn't affect the other player except that they keep their points. So no further action needed.

        # Check for 120 or more
        game_over = False
        winner = None
        for i, p in enumerate(self.players):
            if p.score >= 120:
                # If both cross 120, bidder wins
                game_over = True
        if game_over:
            if self.players[0].score >= 120 and self.players[1].score >= 120:
                # bidder goes out
                winner = self.bid_winner
            elif self.players[0].score >= 120:
                winner = 0
            elif self.players[1].score >= 120:
                winner = 1

        result = {
            "bidder": self.players[self.bid_winner].name,
            "bid": self.bid,
            "bidder_score": self.players[self.bid_winner].score,
            "other_score": self.players[non_bidder_idx].score,
            "highest_card_played": self.highest_card_played,
            "highest_card_owner": self.players[self.highest_card_owner].name if self.highest_card_owner is not None else None,
            "game_over": game_over,
            "winner": self.players[winner].name if winner is not None else None
        }
        return result

###############################################################################
#                             FLASK APP ROUTES                                #
###############################################################################

# We'll store a single global game for demonstration
current_game = None
dealer_index = 1  # Let's fix the dealer as player index 1 ("Computer") for heads-up demonstration
round_trick_count = 0  # track how many tricks have been played in the current round

@app.route("/", methods=["GET"])
def home():
    """
    A simple root route to show a minimal HTML message or instructions.
    """
    return (
        "<h2>Welcome to Heads-Up Forty-Fives (120-Point)!</h2>"
        "<p>Use the following endpoints (POST in JSON) to play:</p>"
        "<ul>"
        "<li>/new_round (POST) - Start or reset a round.</li>"
        "<li>/bid (POST) - Submit your bid, triggers computer's bid logic.</li>"
        "<li>/select_trump (POST) - If you won the bid, call trump.</li>"
        "<li>/attach_kitty (POST) - Bidder takes kitty and discards (auto logic). Then other discards.</li>"
        "<li>/play_trick (POST) - Provide 'lead_card' if it's your lead, else leave it blank to let computer lead.</li>"
        "<li>/finalize_round (POST) - Once 5 tricks have played, finalize scoring.</li>"
        "<li>/show_state (GET) - See your current hand and scores.</li>"
        "</ul>"
    )

@app.route("/new_round", methods=["POST"])
def new_round():
    global current_game, dealer_index, round_trick_count
    # If we have no current game, create one
    if current_game is None:
        current_game = Game()
    else:
        current_game.reset_round_state()

    # Deal
    current_game.deal_hands(dealer_index)
    round_trick_count = 0

    return jsonify({
        "message": "New round dealt.",
        "player_hand": current_game.get_player_hand_strings(0),
        "dealer_index": dealer_index
    })

@app.route("/bid", methods=["POST"])
def bid():
    """
    JSON Body: { "player_bid": 15 } for example
    We do a naive comp bid. If both pass => dealer is forced 15.
    Then we figure out who won. That player will call trump next.
    """
    global current_game, dealer_index
    if current_game is None:
        return jsonify({"error": "No game in progress. Call /new_round first."}), 400

    data = request.get_json() or {}
    player_bid = data.get("player_bid", 0)

    # Perform bidding
    current_game.perform_bidding(dealer_index, player_bid)
    winner_name = current_game.players[current_game.bid_winner].name
    bid_amount = current_game.bid

    return jsonify({
        "message": f"Bidding complete. {winner_name} won the bid at {bid_amount}."
    })

@app.route("/select_trump", methods=["POST"])
def select_trump():
    """
    JSON Body: { "suit": "Hearts" }
    If user is the bidder, pick suit. If the comp is the bidder, it picks automatically.
    """
    global current_game
    if current_game is None:
        return jsonify({"error": "No game in progress. /new_round first."}), 400
    if current_game.bid_winner is None:
        return jsonify({"error": "No bid winner yet. /bid first."}), 400

    bidder = current_game.players[current_game.bid_winner]
    data = request.get_json() or {}
    chosen_suit = data.get("suit")

    if bidder.name == "You":
        # user picks the suit from data
        if not chosen_suit or chosen_suit not in ["Hearts", "Diamonds", "Clubs", "Spades"]:
            return jsonify({"error": "Invalid suit. Must be Hearts, Diamonds, Clubs, or Spades."}), 400
        current_game.set_trump_suit(chosen_suit)
        return jsonify({"message": f"You chose trump: {chosen_suit}."})
    else:
        # computer picks automatically
        comp_suit = current_game.computer_pick_trump_suit()
        current_game.set_trump_suit(comp_suit)
        return jsonify({"message": f"Computer chose trump: {comp_suit}."})

@app.route("/attach_kitty", methods=["POST"])
def attach_kitty():
    """
    Bidder takes kitty, discards to 5, then other player discards, all auto-logic.
    """
    global current_game
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400
    if current_game.bid_winner is None or current_game.trump_suit is None:
        return jsonify({"error": "No trump set yet. /select_trump first."}), 400

    current_game.attach_kitty()
    current_game.allow_other_player_discard()

    return jsonify({
        "message": "Kitty attached and discard phase complete.",
        "player_hand": current_game.get_player_hand_strings(0)
    })

@app.route("/play_trick", methods=["POST"])
def play_trick():
    """
    JSON Body:
    {
      "lead_card": "5 of Clubs"  # if it's the user's lead
    }
    If it's the computer's lead, omit "lead_card" or set to null.
    """
    global current_game, round_trick_count
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400
    if current_game.trump_suit is None:
        return jsonify({"error": "No trump set. /select_trump first."}), 400

    data = request.get_json() or {}
    lead_card_str = data.get("lead_card")

    result = current_game.play_trick(lead_card_str)
    if "error" in result:
        return jsonify(result), 400

    round_trick_count += 1
    return jsonify(result)

@app.route("/finalize_round", methods=["POST"])
def finalize_round():
    """
    Once we've played all 5 tricks, call this to apply bonus trick, check bidder's bid, see if game is over, etc.
    """
    global current_game, round_trick_count, dealer_index
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400
    if round_trick_count < 5:
        return jsonify({"error": "You haven't played all 5 tricks yet."}), 400

    result = current_game.finalize_hand()

    # Possibly rotate dealer if you like. For demonstration, let's always keep the dealer as index 1 (Computer)
    # Or do: dealer_index = 1 - dealer_index

    return jsonify({
        "round_result": result,
        "player_score": current_game.players[0].score,
        "computer_score": current_game.players[1].score
    })

@app.route("/show_state", methods=["GET"])
def show_state():
    """
    Quick debug route to see what's in your hand and current scores, etc.
    """
    global current_game
    if current_game is None:
        return jsonify({"error": "No game in progress."}), 400

    return jsonify({
        "player_hand": current_game.get_player_hand_strings(0),
        "player_score": current_game.players[0].score,
        "computer_hand_count": len(current_game.players[1].hand),
        "computer_score": current_game.players[1].score,
        "bid_winner": current_game.bid_winner,
        "bid": current_game.bid,
        "trump_suit": current_game.trump_suit
    })

###############################################################################
#                                APP RUN                                      #
###############################################################################
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
