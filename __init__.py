"""
Source:
    - Inspiration pour l'agrégation de données de decks Magic: The Gathering:
      https://elvishjerricco.github.io/2015/09/24/automatically-generating-magic-decks.html
"""

import re
from collections import Counter, defaultdict
from itertools import combinations

from mtgdc_carddata import DecklistBuilder
from tqdm import tqdm

from mtgdc_banlist import BanlistCompiler


class Aggregator:
    def __init__(self, decklists: list[str], **kwargs) -> None:
        self.ordre = kwargs.get("ordre", kwargs.get("order", 1))
        self.size = kwargs.get("size", 100)

        use_banlist = kwargs.get("use_banlist", True)

        self.decklists = [
            [
                f"{card} {i}"
                for qty, card in deck
                for i in range(int(qty))
                if not (BanlistCompiler().is_banned(card) and use_banlist)
            ]
            for deck in decklists
        ]

        self.ranking_structure = Counter()
        tmp_collective = Counter()

        for deck in self.decklists:
            tmp = Aggregator.get_combinations(deck, self.ordre)
            tmp_collective.update(deck)
            self.ranking_structure.update(tmp)

        self.collective = set(tmp_collective.keys())
        self._initial_ranking_structure = self.ranking_structure.copy()

    def aggregate(self, **kwargs):
        self.size = kwargs.get("size", self.size)
        action = kwargs.get("action", f"Order {self.ordre}")
        progress_bar = ProgressBar(len(self.collective), self.size, action=action)
        while len(self.collective) > self.size:
            self._remove_cards()
            progress_bar.current_size(len(self.collective))

    def export(self, o_name: str = "mtgdc_aggregation.txt", **kwargs) -> None:
        title = kwargs.get("title", "Barrin's Data Aggregation")
        sortie = [
            f"===== {title} =====",
            f"Nb decks: {len(self.decklists)}",
            f"Ordre {self.ordre}",
            f"Score: {self.robustesse:.4f}",
            "----------",
            DecklistBuilder.build_deck(self.decklist),
        ]

        with open(o_name, "+w", encoding="utf-8") as file:
            file.write("\n".join(sortie))

    def _calculate_ranks(self) -> dict:
        ranks = defaultdict(float)
        updated_ranking = {}
        for combination, count in list(self.ranking_structure.items()):
            if set(combination) <= self.collective:
                updated_ranking[combination] = count
                rank = count * (1 / (2 ** len(combination)))
                for card in combination:
                    ranks[card] += rank
        self.ranking_structure = updated_ranking
        return Aggregator.transpose_dict(dict(ranks))

    def _remove_cards(self) -> None:
        ranks = self._calculate_ranks()
        lowest_rank = min(ranks.keys())
        for card in ranks[lowest_rank]:
            if len(self.collective) > self.size:
                self.collective.remove(card)
            else:
                break

    @property
    def decklist(self) -> list:
        return Counter(
            [Aggregator.remove_numeric_suffix(card) for card in self.collective]
        )

    @property
    def robustesse(self):
        initial_ranks = self._initial_ranking_structure

        rank_changes = {
            card: abs(self.ranking_structure.get(card, 0) - initial_ranks[card])
            for card in initial_ranks
        }

        score = (
            sum(rank_changes.values()) / len(rank_changes)
            if len(rank_changes) > 0
            else float("inf")
        )

        return score

    @staticmethod
    def concatenate(decklist: list) -> list:
        return [f"{qty} {carte}" for carte, qty in sorted(Counter(decklist).items())]

    @staticmethod
    def get_combinations(lst: list, max_size: int) -> list:
        return [
            tuple(sorted(comb))
            for i in range(max_size)
            for comb in combinations(lst, i + 1)
        ]

    @staticmethod
    def remove_numeric_suffix(string: str) -> str:
        cleaned_string = re.sub(r"\d+$", "", string)
        return cleaned_string.strip()

    @staticmethod
    def transpose_dict(input_dict: dict) -> dict:
        output_dict = defaultdict(list)
        for key, value in input_dict.items():
            output_dict[value].append(key)
        return dict(output_dict)


class ProgressBar:
    def __init__(self, start, stop, **kwargs) -> None:
        self._start = start
        self._previous_size = start
        self._stop = stop
        self._progress_bar = None
        self._description = kwargs.get("action", "Processing")

    def current_size(self, current_size) -> None:
        step = (current_size - self._previous_size) / (self._stop - self._start) * 100
        self._previous_size = current_size

        self.progress_bar.update(step)

    @property
    def progress_bar(self) -> tqdm:
        if self._progress_bar is None:
            self._progress_bar = tqdm(
                total=self._stop,
                desc=self._description,
                unit="%",
                bar_format="{desc} |{bar}| {n:.2f}/{total}",
                leave=True,
            )
        return self._progress_bar
