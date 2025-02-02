# game_logic.py

import random

TRUMP_DIAMONDS = { ... }
TRUMP_HEARTS = { ... }
TRUMP_CLUBS = { ... }
TRUMP_SPADES = { ... }
OFFSUIT_DIAMONDS = { ... }
OFFSUIT_HEARTS = { ... }
OFFSUIT_CLUBS = { ... }
OFFSUIT_SPADES = { ... }

def get_card_rank(card_str: str, trump_suit: str) -> int:
    # same logic as before
    ...

def card_back_url():
    return "https://deckofcardsapi.com/static/img/back.png"

def card_to_image_url(card_str):
    # "10" -> "0" logic
    ...

class Card:
    def __init__(self, suit, rank):
        ...
    def __str__(self):
        ...

class Deck:
    def __init__(self):
        ...
    def shuffle(self):
        ...
    def deal(self,n):
        ...

class Player:
    def __init__(self,name):
        ...
    def add_to_hand(self,cards):
        ...

class Game:
    def __init__(self):
        # players, deck, kitty, etc.
        ...
    def rotate_dealer(self):
        ...
    def reset_hand(self):
        ...
    def deal_hands(self):
        ...
    def user_bid(self,bid_val):
        ...
    def set_trump(self,suit=None):
        ...
    def attach_kitty_user(self):
        ...
    def discard_comp(self):
        ...
    def discard_user(self, discardList):
        ...
    def finalize_kitty_user(self, kittyKeep, kittyDiscard):
        ...
    def both_discard_done_check(self):
        ...
    def play_trick_user_lead(self,card_str):
        ...
    def comp_lead_trick(self):
        ...
    def respond_to_comp_lead(self,userCard):
        ...
    def evaluate_trick(self,plays):
        ...
    def record_high_card(self, card_obj, idx):
        ...
    def auto_finalize(self):
        ...
