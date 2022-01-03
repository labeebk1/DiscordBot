import random

card_map = {
    'A': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    '10': 10,
    'J': 10,
    'Q': 10,
    'K': 10
}

class Card:
    def __init__(self):
        self.suit = random.choice([':hearts:', ':spades:', ':clubs:', ':diamonds:'])
        self.card = random.choice(['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'])
        self.value = card_map[self.card]
        
    def __repr__(self):
        return ' '.join([self.suit, self.card])
