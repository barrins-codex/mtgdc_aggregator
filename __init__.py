import re
from collections import Counter
from itertools import combinations


def get_combinations(lst, max_size):
    """Generates combinations from 1 to `max_size` cards from `lst`."""
    tmp = []
    for i in range(1, max_size + 1):
        tmp.extend(combinations(lst, i))
    return tmp


def transpose_ranks(ranks):
    """Transposes the ranking calculated in
    calculate_ranks to have the scores as keys."""
    tmp = {}
    for entry in ranks.items():
        card, rank = entry
        rank = tmp.setdefault(rank, [])
        rank.append(card)
    return tmp


def remove_numeric_suffix(string):
    """Trailing numerics are left after execution of the script."""
    cleaned_string = re.sub(r"\d+$", "", string)
    return cleaned_string.strip()

def concatenate(decklist):
    """Fonction qui recrée une decklist style `X CARTE`."""
    tmp = Counter(decklist)
    tmp = sorted(tmp.items())
    return [f"{qty} {carte}" for carte, qty in tmp]

class Aggregator:
    """Classe qui gère la logique d'aggrégation des decks."""

    def __init__(self, decks, ordre, size):
        self.decks = []
        self.collective = Counter()
        self.ranking_structure = Counter()

        for deck in decks:
            tmp = []
            for qty, card in deck:
                for i in range(qty):
                    tmp.append(f"{card} {i+1}")
            self.decks.append(tmp)
            self.collective.update(tmp)
            self.ranking_structure.update(get_combinations(tmp, ordre))

        while len(self.collective) > size:
            self._remove_lowest_ranked_card(size)

    @property
    def decklist(self):
        """Propriété qui nettoie le collectif final et retourne une liste de cartes."""
        if not hasattr(self, "_decklist") or self._decklist is None:
            decklist = [remove_numeric_suffix(card) for card in self.collective.keys()]
            self._decklist = concatenate(decklist)
        return self._decklist

    def _remove_lowest_ranked_card(self, size):
        """Méthode qui retire la carte la moins bien notée du collectif."""
        ranks = self._calculate_ranks()
        lowest_rank = min(ranks.keys())
        if len(self.collective) - len(ranks[lowest_rank]) >= size:
            for card in ranks[lowest_rank]:
                del self.collective[card]
        else:
            del self.collective[ranks[lowest_rank][0]]

    def _calculate_ranks(self):
        """Calculates the rank of every card in the ranking_structure."""
        ranks = {}
        combinations_to_remove = []
        for combination, count in self.ranking_structure.items():
            if all(card in self.collective for card in combination):
                rank = count * (1 / (2 ** len(combination)))
                for card in combination:
                    ranks[card] = ranks.get(card, 0) + rank
            else:
                combinations_to_remove.append(combination)
        for combination in combinations_to_remove:
            del self.ranking_structure[combination]
        return transpose_ranks(ranks)
