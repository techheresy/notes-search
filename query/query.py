"""
функционал поиска:
  1. поиск слов
  2. ранжирование: как далеко слова могут быть друг от друга
  3. вывод сниппитов результата поиска
* 4. точный поиск: слово обернуто в ковычки, нужен отдельный индекс без нормализации

алгоритм поиска слов:
1. валидация query: подсчет скобок, (*ковычек)
2. подготовить query к парсингу: нормализация, нижний регистр
3. найти все вхождения NOT, NOT OR, NOT AND, OR, AND
4. обход по дереву и выполняем правую часть запроса
"""
import re

from validator.symbolpair import SymbolPair, check_balanced


class Entry:
    def __init__(self, entry):
        self.entry = entry

    def __repr__(self):
        return self.entry


class Binary:
    __parse_symbol__ = None

    def __init__(self, left, right):
        self.left = left
        self.rigth = right

    def __repr__(self):
        return f"{self.left} {self.__parse_symbol__} {self.rigth}"


class NotAnd(Binary):
    __parse_symbol__ = "!|"


class NotOr(Binary):
    __parse_symbol__ = "!&"


class Not(Binary):
    __parse_symbol__ = "!"


class And(Binary):
    __parse_symbol__ = "&"


class Or(Binary):
    __parse_symbol__ = "|"


operator_map = {o.__parse_symbol__: o for o in [Not, NotOr, NotAnd, Or, And]}

operator_patterns = [re.escape(o) for o in operator_map.keys()]
operator_patterns.sort(key=lambda o: len(o), reverse=True)
operator_search_pattern = "|".join(operator_patterns)
group_search_pattern = "|".join(re.escape(g) for g in ["(", ")"])

search_pattern = f"{operator_search_pattern}|{group_search_pattern}"


class Query:
    __symbolpairs__ = [
        SymbolPair("(", ")"),
        SymbolPair("\"", "\""),
    ]

    def __init__(self, query: str):
        self.query = query

    def validate(self) -> None:
        for symbolpair in self.__symbolpairs__:
            check_balanced(symbolpair, self.query)

    def parse(self, query):
        q = query.strip()
        q_start = 0
        q_end = len(q)

        for o in re.finditer(search_pattern, q):
            if operator := operator_map.get(o.group()):
                return operator(
                    left=self.parse(q[q_start:o.start()]),
                    right=self.parse(q[o.end():q_end])
                )
        return Entry(q)


test_queries = [
    ## nodes
    "word2 | word3 | word4 & word5",
    # "(word & word) | (word & word)",
    # "word & (word | word)",

    ## not
    # "!word & !word",
    # "!(word & word)",
    # "word & !(word & word)",

    ## raw-search
    # "!'word'",
    # "'word' & 'word'",
]
for q in test_queries:
    query = Query(q)
    query.validate()
    search_tree = query.parse(q)
    print(search_tree)
