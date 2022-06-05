from dataclasses import dataclass


@dataclass
class SymbolPair:
    opening: str
    closing: str

    def __repr__(self):
        return f"Pair {self.opening} {self.closing}"

    @property
    def equaled(self):
        return self.opening == self.closing

class UnbalancedQuery(Exception):
    def __init__(self, query, position: int):
        self.query = query
        self.position = position

    def __str__(self):
        return f"Unclosed or redundant symbol position={self.position}\n" \
               f"{self.query}\n" \
               f"{(' ' * self.position) + '^'}"


def check_balanced(symbolpair: SymbolPair, query: str):
    if symbolpair.equaled:
        if query.count(symbolpair.opening) % 2 != 0:
            raise UnbalancedQuery(query, query.rfind(symbolpair.opening))
        return

    stack = []

    for position, char in enumerate(query):
        if char == symbolpair.opening:
            stack.append(char)

        elif char == symbolpair.closing:
            if not stack:
                raise UnbalancedQuery(query, position)
            if not _compare(symbolpair, stack.pop(), char):
                raise UnbalancedQuery(query, position)

    if stack:
        raise UnbalancedQuery(query, position)


def _compare(symbolpair: SymbolPair, opening: str, closing: str) -> bool:
    if symbolpair.opening == opening and symbolpair.closing == closing:
        return True
    return False
