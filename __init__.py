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

    - _remove_cards():
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

from mtgdc_banlist.banlist_compiler import BanlistCompiler
from tqdm import tqdm


class Aggregator:
    """A class to aggregate data from Magic: The Gathering decks.

    Attributes:
        collective (set):
            A Counter object storing card frequencies across all decks.
        decklists (list):
            The list of decklists provided for the aggregation.
        ordre (int):
            The order of combinations for ranking.
        ranking_structure (Counter):
            A Counter object storing combination frequencies.

    Methods:
        __init__(self, decks: list[str], **kwargs):
            Initializes the Aggregator instance with deck data and optional parameters.
        aggregate(self, size: int = 100):
            Aggregates the card data to a specified size by removing lowest ranked cards.
        export(self, o_name: str = "mtgdc_aggregation.txt") -> None:
            Exports the aggregated data to a file.
        _calculate_ranks(self) -> dict:
            Calculates ranks for cards based on combination frequencies.
        _remove_cards(self):
            Removes the lowest ranked cards from the collective data.
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

    def __init__(self, decklists: list[str], **kwargs) -> None:
        self.ordre = kwargs.get("ordre", 1)
        self.size = kwargs.get("size", 100)

        self.decklists = [
            [
                f"{card} {i}"
                for qty, card in deck
                for i in range(int(qty))
                if not BanlistCompiler().is_banned(card)
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
        """Aggregate the card data to a specified size by removing lowest ranked cards.

        Args:
            **kwargs: Arguments supplémentaires pour personnaliser la barre de progression.
                action (str, optional): La description de l'action en cours. Par défaut, "Ordre k".
                size (int, optional): The target size for the aggregated card data.

        """
        self.size = kwargs.get("size", self.size)
        action = kwargs.get("action", f"Order {self.ordre}")
        progress_bar = ProgressBar(len(self.collective), self.size, action=action)
        while len(self.collective) > self.size:
            self._remove_cards()
            progress_bar.current_size(len(self.collective))

    def export(self, o_name: str = "mtgdc_aggregation.txt", **kwargs) -> None:
        """Aggregate the card data to a specified size by removing lowest ranked cards.

        Args:
            size (int): The target size for the aggregated card data.

        Keyword Args:
            title (str): Title displayed in the output file.
        """
        title = kwargs.get("title", "Barrin's Data Aggregation")
        sortie = [
            f"===== {title} =====",
            f"Nb decks: {len(self.decklists)}",
            f"Ordre {self.ordre}",
            f"Score: {self.robustesse:.4f}",
            "----------",
        ]

        with open(o_name, "+w", encoding="utf-8") as file:
            file.write("\n".join(sortie + self.decklist))

    def _calculate_ranks(self) -> dict:
        """Calculate ranks for cards based on combination frequencies.

        Returns:
            dict: A dictionary with card names as keys and their respective ranks as values.
        """
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
        """Aggregate the card data to a specified size by removing lowest ranked cards."""
        ranks = self._calculate_ranks()
        lowest_rank = min(ranks.keys())
        for card in ranks[lowest_rank]:
            if len(self.collective) > self.size:
                self.collective.remove(card)
            else:
                break

    @property
    def decklist(self) -> list:
        """Generate a decklist based on the aggregated card data.

        Returns:
            list: A list of strings representing the decklist.
        """
        return Aggregator.concatenate(
            [Aggregator.remove_numeric_suffix(card) for card in self.collective]
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
    def concatenate(decklist: list) -> list:
        """Concatenate card names with their quantities.

        Args:
            decklist (list): A list of card names.

        Returns:
            list: A list of concatenated strings representing card names with quantities.
        """
        return [f"{qty} {carte}" for carte, qty in sorted(Counter(decklist).items())]

    @staticmethod
    def get_combinations(lst: list, max_size: int) -> list:
        """Generate combinations from a list up to a specified maximum size.

        Args:
            lst (list): The list of elements to generate combinations from.
            max_size (int): The maximum size of combinations to generate.

        Returns:
            list: A list of combinations.
        """
        return [
            tuple(sorted(comb))
            for i in range(max_size)
            for comb in combinations(lst, i + 1)
        ]

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


class ProgressBar:
    """Classe pour créer une barre de progression visuelle.

    Utilitaire pour gérer une barre de progression visuelle.

    Ce module définit la classe 'ProgressBar' pour créer et gérer une barre de progression visuelle
    utilisant la bibliothèque 'tqdm'. La barre de progression affiche l'avancement d'une opération
    sur une plage donnée.

    Classes:
        ProgressBar: Classe pour créer et gérer une barre de progression visuelle.

    Usage:
        from tqdm import tqdm
        from progress_bar_utility import ProgressBar

        # Exemple d'utilisation de la classe ProgressBar
        start_value = 0
        stop_value = 100
        progress_bar = ProgressBar(start_value, stop_value, action="Traitement en cours")

        for i in range(start_value, stop_value):
            # Effectuer l'opération
            # Mettre à jour la taille actuelle
            progress_bar.current_size(i)
        # La barre de progression se met à jour automatiquement avec chaque appel à 'current_size'.

    Args:
        start (int): La valeur de départ pour la barre de progression.
        stop (int): La valeur de fin pour la barre de progression.
        **kwargs: Arguments supplémentaires pour personnaliser la barre de progression.
            action (str, optional): La description de l'action en cours. Par défaut, "Processing".

    Attributes:
        _start (int): La valeur de départ pour la barre de progression.
        _previous_size (int): La taille précédente de la barre de progression.
        _stop (int): La valeur de fin pour la barre de progression.
        _progress_bar (tqdm): L'objet tqdm représentant la barre de progression.
        _description (str): La description de l'action en cours.

    """

    def __init__(self, start, stop, **kwargs) -> None:
        self._start = start
        self._previous_size = start
        self._stop = stop
        self._progress_bar = None
        self._description = kwargs.get("action", "Processing")

    def current_size(self, current_size) -> None:
        """Met à jour la taille actuelle de la barre de progression.

        Args:
            current_size (int): La taille actuelle pour mettre à jour la barre de progression.
        """
        step = (current_size - self._previous_size) / (self._stop - self._start) * 100
        self._previous_size = current_size

        self.progress_bar.update(step)

    @property
    def progress_bar(self) -> tqdm:
        """Obtient l'objet tqdm représentant la barre de progression.

        Returns:
            tqdm: L'objet tqdm représentant la barre de progression.
        """
        if self._progress_bar is None:
            self._progress_bar = tqdm(
                total=self._stop,
                desc=self._description,
                unit="%",
                bar_format="{desc} |{bar}| {n:.2f}/{total}",
                leave=True,
            )
        return self._progress_bar
