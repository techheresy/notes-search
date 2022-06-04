from dataclasses import dataclass


@dataclass
class SymbolPair:
    left: str
    right: str

    def __repr__(self):
        return f"Pair {self.left} {self.right}"


class UnbalancedQuery(Exception):
    def __init__(self, query, position: int):
        self.query = query
        self.position = position

    def __str__(self):
        return f"Unclosed or redundant symbol position={self.position}\n" \
               f"{self.query}\n" \
               f"{(' ' * self.position) + '^'}"


def check_balanced(symbolpair: SymbolPair, query: str):
    if symbolpair.left == symbolpair.right:
        if query.count(symbolpair.left) % 2 != 0:
            raise UnbalancedQuery(query, query.rfind(symbolpair.left))
        return

    stack = []

    for position, char in enumerate(query):
        if char == symbolpair.left:
            stack.append(char)

        elif char == symbolpair.right:
            if len(stack) == 0:
                raise UnbalancedQuery(query, position)
            if not _compare(symbolpair, stack.pop(), char):
                raise UnbalancedQuery(query, position)

    if len(stack) != 0:
        raise UnbalancedQuery(query, position)


def _compare(symbolpair: SymbolPair, opening: str, closing: str) -> bool:
    if symbolpair.left == opening and symbolpair.right == closing:
        return True
    return False
