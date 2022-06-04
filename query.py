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
from validator.symbolpair import SymbolPair, check_balanced


class Query:
    __symbolpairs__ = [
        SymbolPair("(", ")"),
        SymbolPair("\"", "\""),
    ]

    def __init__(self, query: str):
        self.query = self.validate(query)

    def validate(self, query: str) -> None:
        for symbolpair in self.__symbolpairs__:
            check_balanced(symbolpair, query)


Query("()()()\"()\"\"")
