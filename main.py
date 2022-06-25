import glob
import logging
import os.path
import pickle
import re
import sys
from collections import defaultdict
from typing import List, Dict

import pymorphy2
from nltk.corpus import stopwords
from nltk.downloader import download
from nltk.tokenize import word_tokenize

download("stopwords")
download("punkt")

MIN_SCORE = -sys.maxsize
RU = "russian"
RE_ONLY_WORDS = re.compile("[\W_]+")

logging.getLogger().setLevel(logging.INFO)


class Tokenizer:
    def __init__(self):
        self.morph_analyzer = pymorphy2.MorphAnalyzer()
        self.stopwords = stopwords.words(RU)

    def word_normalizer(self, word: str) -> str:
        normalized_words = self.morph_analyzer.parse(word)

        word_index = 0

        if len(normalized_words) > 1:
            word_score = MIN_SCORE

            for index, morph_word in enumerate(normalized_words):
                if morph_word.score > word_score:
                    word_score = morph_word.score
                    word_index = index

        return normalized_words[word_index].normal_form

    def tokenize_text(self, text: str) -> List[str]:
        only_words_text = RE_ONLY_WORDS.sub(" ", text.lower())
        tokenized_text: List[str] = word_tokenize(only_words_text, language=RU)

        tokens: List[str] = []
        for word in tokenized_text:
            if word not in self.stopwords:
                normalized_word = self.word_normalizer(word)
                if len(normalized_word) > 1:
                    tokens.append(normalized_word)

        return tokens


class Document:
    def __init__(self, uid: str):
        self.uid = uid
        self.text: str = ""
        self.tokens = None

    @staticmethod
    def load_text_from_txt(path: str, uid: str):
        doc = Document(uid)
        with open(path, "r") as f:
            doc.text = f.read()
        return doc


class Index:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def build_revert_index(self, docs: List[Document]):
        indicies = {}
        revert_index = defaultdict(list)

        logging.info(f"tokenize {len(docs)} docs")
        for doc in docs:
            logging.info(f"tokenize doc: uid={doc.uid} len={len(doc.text)}")
            tokens = self.tokenizer.tokenize_text(doc.text)
            indicies[doc.uid] = self.tokens_indexation(tokens)

        logging.info(f"building revert index, from {len(docs)} docs")
        for doc_uid, token_positions in indicies.items():
            token_positions: Dict[str, List[int]]

            logging.info(f"appending uid={doc_uid} to revert index")
            for token, positions in token_positions.items():
                revert_index[token].append({doc_uid: positions})

        logging.info("build revert index finished")
        return revert_index

    def tokens_indexation(self, tokens: List[str]) -> Dict[str, List[int]]:
        token_positions = defaultdict(list)

        for index, token in enumerate(tokens):
            token_positions[token].append(index)

        return token_positions


if __name__ == "__main__":
    dump_file = "revert_index.pickle"
    build_force = False

    if build_force or not os.path.exists(dump_file):
        logging.info("build revert index")
        docs, files_path = [], glob.glob("mock_news/*.txt")

        for fp in files_path:
            uid = "".join([n for n in fp if n.isdigit()])
            docs.append(Document.load_text_from_txt(fp, uid))

        docs.sort(key=lambda doc: int(doc.uid))

        tokenizer = Tokenizer()

        index = Index(tokenizer=tokenizer)
        revert_index = index.build_revert_index(docs)

        with open(dump_file, "wb") as f:
            pickle.dump(revert_index, f)
            f.close()
    else:
        logging.info("dump file found, revert index loaded")
        with open(dump_file, "rb") as f:
            revert_index = pickle.load(f)
            f.close()