class Player:
    def __init__(self, name):
        self.legal_positions = []
        self.name = name

    def __str__(self):
        return self.name
