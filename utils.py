"""
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

"""
from tqdm import tqdm


class ProgressBar:
    """Classe pour créer une barre de progression visuelle.

    Cette classe utilise la bibliothèque 'tqdm' pour afficher une barre de progression visuelle.

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
