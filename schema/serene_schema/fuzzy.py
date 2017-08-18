

#spelling corrector code from norvig.com/spell-correct.html

import re, collections

alphabet = 'abcdefghijklmnopqrstuvwxyz'

class SpellChecker(object):

    def __init__(self):
        self.MODEL = collections.defaultdict(lambda : 1)

    def train(self, features):
        for f in features:
            self.MODEL[f.lower()] += 1

    def edits1(self, word):
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a,b in splits if len(b) > 1]
        replaces = [a + c + b[1:] for a,b in splits for c in alphabet if b]
        inserts = [a + c + b for a,b in splits for c in alphabet]
        return set(deletes + transposes + replaces + inserts)

    def known_edits2(self, word):
        return set(e2 for e1 in self.edits1(word) for e2 in self.edits1(e1) if e2 in self.MODEL)

    def known(self, words):
        return set(w for w in words if w in self.MODEL)

    def correct(self, word):
        word = word.lower()
        candidates = self.known([word]) or self.known(self.edits1(word)) or self.known_edits2(word) or [word]
        suggestion = max(candidates, key=self.MODEL.get)
        if suggestion == word:
            return None
        return suggestion



def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def find_ngrams(word, n):
    return [''.join(_) for _ in zip(*[word[i:] for i in range(n)])]

n_RANGE = (2,4)

class TFIDF(object):

    def __init__(self, names):
        self.lookup = collections.defaultdict(list)

        for name in names:
            for l in range(*n_RANGE):
                for gram in find_ngrams(name.lower().replace(' ',''), l):
                    self.lookup[gram].append(name)

    def add_other(self, others):
        """
        Take alternatives mappings in a list of tuple(input, output) pairs
        where a match on input returns output...
        """

        for in_name, out_name in others:
            for l in range(*n_RANGE):
                for gram in find_ngrams(in_name.lower().replace(' ',''), l):
                    self.lookup[gram].append(out_name)

    def match(self, _name):

        name = _name.lower().replace(' ','')

        scores = collections.defaultdict(float)

        n_min, n_max = n_RANGE

        for l in range(n_min, n_max):

            for gram in find_ngrams(name, l):
                for suggestion in self.lookup[gram]:
                    score = float(l)/len(self.lookup[gram])
                    scores[suggestion] += score/max(1, levenshtein(name, suggestion.lower().replace(' ','')))

        if not scores:
            raise ValueError('No matches at all for {}'.format(name))

        return sorted(scores.iteritems(), key=lambda k: k[1], reverse=True)[0][0]








