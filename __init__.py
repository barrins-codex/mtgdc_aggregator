"""
Module de traitement et d'agrégation des données de decks Magic: The Gathering.

Ce module fournit une classe Aggregator permettant d'agréger les données de plusieurs decks
de Magic: The Gathering en calculant des statistiques sur les cartes et leurs combinaisons.

Source:
    - Inspiration pour l'agrégation de données de decks Magic: The Gathering:
      https://elvishjerricco.github.io/2015/09/24/automatically-generating-magic-decks.html

Classe:
    Aggregator: Classe principale pour agréger les données de decks.

Méthodes:
    - __init__(decks: list[str], **kwargs):
        Initialise l'instance Aggregator avec les données des decks et des paramètres optionnels.

    - aggregate(size: int = 100):
        Agrège les données des cartes pour atteindre une taille spécifiée
        en supprimant les cartes les moins bien classées.

    - export(o_name: str = "mtgdc_aggregation.txt") -> None:
        Exporte les données agrégées vers un fichier.

    - _remove_lowest_ranked_card(size: int):
        Supprime les cartes les moins bien classées des données collectives.

    - _calculate_ranks() -> dict:
        Calcule les classements des cartes en fonction des fréquences de combinaison.

    - decklist() -> list:
        Génère une liste de deck basée sur les données agrégées de cartes.

    - robustesse():
        Calcule un score représentant la robustesse de l'agrégation.

Fonctions statiques:
    - get_combinations(lst: list, max_size: int) -> list:
        Génère des combinaisons à partir d'une liste jusqu'à une taille maximale spécifiée.

    - transpose_dict(input_dict: dict) -> dict:
        Transpose un dictionnaire en échangeant clés et valeurs.

    - remove_numeric_suffix(string: str) -> str:
        Supprime les suffixes numériques des chaînes de caractères.

    - concatenate(decklist: list) -> list:
        Concatène les noms de cartes avec leurs quantités.
"""
import re
from collections import Counter, defaultdict
from itertools import combinations


class Aggregator:
    """A class to aggregate data from Magic: The Gathering decks.

    Attributes:
        ordre (int):
            The order of combinations for ranking.
        nb_decks (int):
            The number of decks aggregated.
        collective (Counter):
            A Counter object storing card frequencies across all decks.
        ranking_structure (Counter):
            A Counter object storing combination frequencies.
        _initial_ranking_structure (Counter):
            A Counter object storing the initial combination frequencies.

    Methods:
        __init__(self, decks: list[str], **kwargs):
            Initializes the Aggregator instance with deck data and optional parameters.
        aggregate(self, size: int = 100):
            Aggregates the card data to a specified size by removing lowest ranked cards.
        export(self, o_name: str = "mtgdc_aggregation.txt") -> None:
            Exports the aggregated data to a file.
        _remove_lowest_ranked_card(self, size: int):
            Removes the lowest ranked cards from the collective data.
        _calculate_ranks(self) -> dict:
            Calculates ranks for cards based on combination frequencies.
        decklist(self) -> list:
            Generates a decklist based on the aggregated card data.
        robustesse(self):
            Calculates a score representing the robustness of the aggregation.
        get_combinations(lst: list, max_size: int) -> list:
            Generates combinations from a list up to a specified maximum size.
        transpose_dict(input_dict: dict) -> dict:
            Transposes a dictionary, switching keys and values.
        remove_numeric_suffix(string: str) -> str:
            Removes numeric suffixes from strings.
        concatenate(decklist: list) -> list:
            Concatenates card names with their quantities.
    """

    def __init__(self, decks: list[str], ordre: int = 1):
        self.ordre = ordre

        self.nb_decks = 0
        self.collective = Counter()
        self.ranking_structure = Counter()

        for deck in decks:
            tmp = [f"{card} {i+1}" for qty, card in deck for i in range(int(qty))]
            tmp_combinations = Aggregator.get_combinations(tmp, self.ordre)

            self.nb_decks += 1
            self.collective.update(tmp)
            self.ranking_structure.update(tmp_combinations)

        self._initial_ranking_structure = self.ranking_structure.copy()

    def aggregate(self, size: int = 100):
        """Aggregate the card data to a specified size by removing lowest ranked cards.

        Args:
            size (int): The target size for the aggregated card data.
        """
        while len(self.collective) > size:
            self._remove_lowest_ranked_card(size)

    def export(self, o_name: str = "mtgdc_aggregation.txt") -> None:
        """Aggregate the card data to a specified size by removing lowest ranked cards.

        Args:
            size (int): The target size for the aggregated card data.
        """
        sortie = [
            "===== Barrin's Data Aggregation =====",
            f"Nb decks: {self.nb_decks}",
            f"Ordre {self.ordre}",
            f"Score: {self.robustesse:.4f}",
            "----------",
        ]

        with open(o_name, "+w", encoding="utf-8") as file:
            file.write("\n".join(sortie + self.decklist))

    def _remove_lowest_ranked_card(self, size: int):
        """Aggregate the card data to a specified size by removing lowest ranked cards.

        Args:
            size (int): The target size for the aggregated card data.
        """
        ranks = self._calculate_ranks()
        lowest_rank = min(ranks.keys())
        for card in ranks[lowest_rank]:
            if len(self.collective) > size:
                del self.collective[card]

    def _calculate_ranks(self) -> dict:
        """Calculate ranks for cards based on combination frequencies.

        Returns:
            dict: A dictionary with card names as keys and their respective ranks as values.
        """
        ranks = defaultdict(float)
        card_collective = set(self.collective.keys())
        updated_ranking = {}
        for combination, count in list(self.ranking_structure.items()):
            if set(combination) <= card_collective:
                rank = count * (1 / (2 ** len(combination)))
                for card in combination:
                    ranks[card] += rank
                updated_ranking[combination] = count
        self.ranking_structure = updated_ranking
        return Aggregator.transpose_dict(dict(ranks))

    @property
    def decklist(self) -> list:
        """Generate a decklist based on the aggregated card data.

        Returns:
            list: A list of strings representing the decklist.
        """
        return Aggregator.concatenate(
            [Aggregator.remove_numeric_suffix(card) for card in self.collective.keys()]
        )

    @property
    def robustesse(self):
        """Calculate a score representing the robustness of the aggregation.

        Returns:
            float: The robustness score.
        """
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
    def get_combinations(lst: list, max_size: int) -> list:
        """Generate combinations from a list up to a specified maximum size.

        Args:
            lst (list): The list of elements to generate combinations from.
            max_size (int): The maximum size of combinations to generate.

        Returns:
            list: A list of combinations.
        """
        return [comb for i in range(max_size) for comb in combinations(lst, i + 1)]

    @staticmethod
    def transpose_dict(input_dict: dict) -> dict:
        """Transpose a dictionary, switching keys and values.

        Args:
            input_dict (dict): The input dictionary to transpose.

        Returns:
            dict: The transposed dictionary.
        """
        output_dict = defaultdict(list)
        for key, value in input_dict.items():
            output_dict[value].append(key)
        return dict(output_dict)

    @staticmethod
    def remove_numeric_suffix(string: str) -> str:
        """Remove numeric suffixes from strings.

        Args:
            string (str): The input string.

        Returns:
            str: The cleaned string without numeric suffixes.
        """
        cleaned_string = re.sub(r"\d+$", "", string)
        return cleaned_string.strip()

    @staticmethod
    def concatenate(decklist: list) -> list:
        """Concatenate card names with their quantities.

        Args:
            decklist (list): A list of card names.

        Returns:
            list: A list of concatenated strings representing card names with quantities.
        """
        return [f"{qty} {carte}" for carte, qty in sorted(Counter(decklist).items())]
