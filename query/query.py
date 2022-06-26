import re
from abc import abstractmethod

from validator.symbolpair import SymbolPair, check_balanced, MalformedQuery


class Entry:
    def __init__(self, entry, invert=False):
        self.entry = entry
        self.invert = invert

    def __repr__(self):
        return f"{'!' if self.invert else ''}{self.entry}"

    def evaluate(self, doc):
        pass


class Binary:
    __parse_symbol__ = None

    def __init__(self, left, right, invert=False):
        self.left = left
        self.right = right
        self.invert = invert

    def __repr__(self):
        return f"{'!' if self.invert else ''}({self.left} {self.__parse_symbol__} {self.right})"

    @abstractmethod
    def evaluate(self, doc):
        raise NotImplemented


class NotAnd(Binary):
    __parse_symbol__ = "!|"

    def evaluate(self, doc):
        if not self.left.evaluate(doc):
            return False
        return not self.right.evaluate(doc)


class And(Binary):
    __parse_symbol__ = "&"

    def evaluate(self, doc):
        if not self.left.evaluate(doc) or not self.right.evaluate(doc):
            return False
        return True


class NotOr(Binary):
    __parse_symbol__ = "!&"

    def evaluate(self, doc):
        if self.left.evaluate(doc) or self.right.evaluate(doc):
            return False
        return True


class Or(Binary):
    __parse_symbol__ = "|"

    def evaluate(self, doc):
        if self.left.evaluate(doc) or self.right.evaluate(doc):
            return True
        return False


# class Not:
#     __parse_symbol__ = "!"


operator_map = {o.__parse_symbol__: o for o in [NotOr, NotAnd, Or, And]}

operator_patterns = [re.escape(o) for o in operator_map.keys()]
operator_patterns.sort(key=lambda o: len(o), reverse=True)
operator_search_pattern = "|".join(operator_patterns)
group_search_pattern = "|".join(re.escape(g) for g in ["(", ")"])

search_pattern = f"{operator_search_pattern}|{group_search_pattern}"


class SearchTree:
    __symbolpairs__ = {
        "group": SymbolPair("(", ")"),
    }

    def __init__(self):
        self.search_tree = None

    def check_balance(self, query, raising=False) -> bool:
        for symbolpair in self.__symbolpairs__.values():
            try:
                check_balanced(symbolpair, query)
            except Exception as e:
                if raising:
                    raise e
                return False
        return True

    def check_malformed_near_symbolpair(self, query):
        symbolpair = self.__symbolpairs__.get("group")
        service_symbols = [" ", "(", ")"]
        bidirectional_symbols = [*operator_map.keys(), *service_symbols]
        forward_symbols = ["!", *service_symbols]

        for idx, symbol in enumerate(query):
            if symbol == symbolpair.opening:
                if idx:
                    count = 1
                    while True:
                        index = idx - count
                        if index != -1:
                            stepback = query[index]
                            count += 1
                            if stepback in operator_map.keys():
                                break
                            if stepback not in forward_symbols:
                                raise MalformedQuery(query, index)
                        else:
                            break
            if symbol == symbolpair.closing:
                count = 1
                while True:
                    index = idx + count
                    if index != len(query):
                        stepforward = query[index]
                        count += 1
                        if stepforward in operator_map.keys():
                            break
                        if stepforward not in bidirectional_symbols:
                            raise MalformedQuery(query, index)
                    else:
                        break

    def strip_group(self, query):
        query = query.strip()

        symbolpair = self.__symbolpairs__.get("group")
        count_opening = 0

        for i in range(len(query) - 1):
            symbol = query[i]

            if symbol == symbolpair.opening:
                count_opening += 1
            elif symbol == symbolpair.closing:
                count_opening -= 1

            if i > 0 and count_opening == 0:
                return query

        if query[0] == symbolpair.opening and query[-1] == symbolpair.closing:
            return query[1:-1]
        return query

    def parse(self, query):
        operator, query_part = None, None

        query_start = 0
        query_end = len(query)

        for o in re.finditer(operator_search_pattern, query):
            query_part = query[query_start:o.start()]
            if self.check_balance(query_part):
                operator = o
                break

        if not operator and self.check_balance(query, raising=True):
            return Entry(query)

        left_part = self.strip_group(query[query_start:operator.start()])
        right_part = self.strip_group(query[operator.end():query_end])

        if operator and (operator_class := operator_map.get(operator.group())):
            return operator_class(
                left=self.parse(left_part),
                right=self.parse(right_part)
            )

    def prepare_query(self, query):
        query = query.strip()
        self.check_malformed_near_symbolpair(query)
        self.check_balance(query, raising=True)
        return self.strip_group(query)

    def build_from_query(self, query):
        query = self.prepare_query(query)
        self.search_tree = self.parse(query)
        return self.search_tree


test_queries = [
    ## nodes
    "((word1 | word2) | word3) & ((word1 | word2) | word3) & (word4 & word5) ошибка",
    "ошибка    (word & word2)",

    ## not
    # "!word & !word",
    # "!(word & word)",
    # "word & !(word & word)",

    ## raw-search
    # "!'word'",
    # "'word' & 'word'",
]
for test_query in test_queries:
    print(test_query)
    search_tree = SearchTree()
    search_tree.build_from_query(test_query)
