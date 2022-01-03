import random

suits = ["spades", "hearts", "clubs", "diamonds"]
suits_values = {"spades":":spades:", "hearts":":hearts:", "clubs": ":clubs:", "diamonds": ":diamonds:"}
cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
cards_values = {"A": 11, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "10":10, "J":10, "Q":10, "K":10}

class Card:
    def __init__(self):
        self.draw()
    
    def draw(self):
        self.suit = random.choice(suits)
        self.suits_value = suits_values[self.suit]
        self.card = random.choice(cards)
        self.card_value = cards_values[self.card]