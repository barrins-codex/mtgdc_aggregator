import re
from collections import Counter, defaultdict
from itertools import combinations
from threading import Lock, Thread


def get_combinations(lst: list, max_size: int) -> list:
    return [comb for i in range(1, max_size + 1) for comb in combinations(lst, i)]


def transpose_dict(input_dict: dict) -> dict:
    output_dict = defaultdict(list)
    for key, value in input_dict.items():
        output_dict[value].append(key)
    return dict(output_dict)


def remove_numeric_suffix(string: str) -> str:
    cleaned_string = re.sub(r"\d+$", "", string)
    return cleaned_string.strip()


def concatenate(decklist: list) -> list:
    return [f"{qty} {carte}" for carte, qty in sorted(Counter(decklist).items())]


class Aggregator:
    def __init__(self, decks: list[str], ordre: int = 3, size: int = 100):
        self.decks = []
        self.collective = Counter()
        self.ranking_structure = Counter()
        self._initial_params = (decks, ordre, size)
        self._initial_collective = Counter()
        self._initial_ranking_structure = Counter()

        self._build_structures()
        self._perform_aggregation()

    def _build_structures(self) -> None:
        decks, ordre, _ = self._initial_params

        for deck in decks:
            tmp = [f"{card} {i+1}" for qty, card in deck for i in range(int(qty))]
            tmp_combinations = get_combinations(tmp, ordre)

            self.decks.append(tmp)
            self.collective.update(tmp)
            self.ranking_structure.update(tmp_combinations)

        self._initial_collective = self.collective.copy()
        self._initial_ranking_structure = self.ranking_structure.copy()

    def _perform_aggregation(self) -> None:
        _, _, size = self._initial_params

        while len(self.collective) > size:
            self._remove_lowest_ranked_card(size)

    @property
    def decklist(self) -> list:
        return concatenate(
            [remove_numeric_suffix(card) for card in self.collective.keys()]
        )

    def _remove_lowest_ranked_card(self, size: int):
        ranks = self._calculate_ranks()
        lowest_rank = min(ranks.keys())
        if len(self.collective) - len(ranks[lowest_rank]) >= size:
            for card in ranks[lowest_rank]:
                del self.collective[card]
        else:
            del self.collective[ranks[lowest_rank][0]]

    def _calculate_ranks(self) -> dict:
        ranks = defaultdict(float)
        card_collective = set(self.collective.keys())
        updated_ranking = Counter()
        for combination, count in list(self.ranking_structure.items()):
            if set(combination) <= card_collective:
                rank = count * (1 / (2 ** len(combination)))
                for card in combination:
                    ranks[card] += rank
                updated_ranking[combination] = count
        self.ranking_structure = updated_ranking
        return transpose_dict(dict(ranks))

    @property
    def robustesse(self):
        initial_ranks = self._initial_ranking_structure
        final_ranks = self.ranking_structure

        rank_changes = {
            card: abs(final_ranks.get(card, 0) - initial_ranks[card])
            for card in initial_ranks
        }
        robustness_score = (
            sum(rank_changes.values()) / len(rank_changes)
            if len(rank_changes) > 0
            else float("inf")
        )

        return robustness_score

    def export(self, o_name: str = "mtgdc_aggregation.txt") -> None:
        decks, ordre, _ = self._initial_params
        sortie = [
            f"===== Barrin's Data Aggregation =====",
            f"Nb decks: {len(decks)}",
            f"Ordre {ordre}",
            f"Score: {self.robustesse:.4f}",
            "----------",
        ]
        sortie.extend(self.decklist)
        sortie.extend(
            [
                "----------",
                "IMPORTANT: Le deck généré ci-après est le fruit de l'aggrégation de",
                "decks déposés sur MTGTOP8. L'équipe Barrin's Data ne saurait être",
                "tenue responsable de la qualité des données saisies par les utilisateurs",
                "tiers du service MTGTOP8.",
            ]
        )

        with open(o_name, "+w", encoding="utf-8") as file:
            file.write("\n".join(sortie))
