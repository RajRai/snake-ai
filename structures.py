class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def as_list(self):
        return [self.x, self.y]

    def as_tuple(self):
        return self.x, self.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return Position(x, y)

    def __sub__(self, other):
        neg = other * -1
        return self + neg

    def __mul__(self, other):
        x = self.x * other
        y = self.y * other
        return Position(x, y)

    __rmul__ = __mul__

    def __str__(self):
        return f"({self.x}, {self.y})"

class Queue:
    def __init__(self):
        self.queue = []

    def __iter__(self):
        return self.queue.__iter__()

    def __len__(self):
        return len(self.queue)

    def is_empty(self):
        return self.queue.len == 0

    def push(self, obj):
        self.queue.append(obj)

    def pop(self):
        return self.queue.pop(0)

    def peek(self, index=0):
        return self.queue[index]

    def insert(self, index, obj):
        self.queue.insert(index, obj)