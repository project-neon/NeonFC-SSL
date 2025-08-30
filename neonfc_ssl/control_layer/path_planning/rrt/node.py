class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = 0

    def __str__(self):
        return f"Node(x={self.x}, y={self.y})"

    def __repr__(self):
        return str(self)
