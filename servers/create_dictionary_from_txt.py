from tools.spell_check import Dictionary
import numpy as np

with open('C:\\Users\\danie\\langserver\\servers\\test_data\\aak-aak.txt', 'r', encoding='utf-8') as f:
    text = f.read()

words = text.split(" ")
unique_words = list(set(words))[:1000]
size = len(unique_words)
print("size: ", size)
dictionary = Dictionary('aak-dictionary')

for idx, word in enumerate(unique_words):
    print((idx / size) * 100)
    dictionary.define(word, 'verified')
