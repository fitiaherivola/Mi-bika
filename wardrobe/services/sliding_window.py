"""
Fenêtre glissante pour gérer l'historique des vêtements portés.

Permet d'éviter de porter le même vêtement trop souvent en conservant
une mémoire des X derniers jours (ou X dernières tenues).

Implémentation : deque (double-ended queue) de taille fixe = O(1) push/pop.
Alternative : file circulaire avec array + index modulo.

Complexité :
  - Ajout d'un port : O(1)
  - Vérification "déjà porté récemment" : O(window_size) dans le pire cas
    (mais window_size petit ~ 7-30 jours → acceptable)

Usage :
    window = RecentWearWindow(utilisateur, jours=7)
    if window.a_ete_porte_recemment(vetement_id):
        # skip
    else:
        # propose
    window.ajouter_port(vetement_id)  # quand tenue portée
"""

from datetime import date, timedelta
from collections import deque

from django.utils import timezone

from wardrobe.models import Vetement


class RecentWearWindow:
    """
    Fenêtre glissante des vêtements portés récemment.

    Stocke en mémoire (cache) + en base via HistoriquePort modèle à créer.
    Pour le prototype, on peut utiliser seulement Tenue.objects.filter(date_creation récente)
    mais pour O(1) on garde un deque en RAM + persistance optionnelle.
    """

    def __init__(self, utilisateur, jours: int = 7, max_entries: int = 50):
        """
        Args:
            utilisateur: instance Utilisateur
            jours:       fenêtre temporelle en jours (défaut 7)
            max_entries: limite du deque (protection mémoire)
        """
        self.utilisateur  = utilisateur
        self.jours        = jours
        self.max_entries  = max_entries
        # Deque de tuples (vetement_id, date_port)
        self.window       = deque(maxlen=max_entries)
        self._charger_historique()

    def _charger_historique(self):
        """
        Charge l'historique depuis les vêtements effectivement portés (last_worn).
        Les tenues générées mais non portées ne comptent pas dans l'anti-répétition.
        """
        date_limite = timezone.now() - timedelta(days=self.jours)
        vetements = Vetement.objects.filter(
            utilisateur=self.utilisateur,
            last_worn__gte=date_limite,
        ).order_by('-last_worn')[:self.max_entries]

        for v in vetements:
            self.window.append((v.id, v.last_worn.date()))

    def a_ete_porte_recemment(self, vetement_id: int) -> bool:
        """
        Vérifie si le vêtement a été porté dans la fenêtre glissante.

        Complexité : O(window_size) — window_size ~ 30-50 → acceptable.
        """
        for (vid, date_port) in self.window:
            if vid == vetement_id:
                # Vérifier si dans la fenêtre temporelle
                if (date.today() - date_port).days <= self.jours:
                    return True
        return False

    def ajouter_port(self, vetement_id: int, date_port=None):
        """
        Ajoute un port de vêtement dans la fenêtre.
        Appelé quand une tenue est effectivement portée (notée).
        """
        if date_port is None:
            date_port = date.today()
        self.window.append((vetement_id, date_port))
        # Optionnel : persister en base ?Pas obligatoire pour prototype

    def nettoyer(self):
        """
        Nettoie les entrées hors fenêtre (date trop ancienne).
        À appeler périodiquement.
        """
        cutoff = date.today() - timedelta(days=self.jours)
        while self.window and self.window[0][1] < cutoff:
            self.window.popleft()

    def get_recent_ids(self) -> list:
        """
        Retourne la liste des IDs récents (pour passer à backtracking, etc.).
        """
        cutoff = date.today() - timedelta(days=self.jours)
        return [vid for (vid, d) in self.window if d >= cutoff]


# ─────────────────────────────────────────
#  POINT D'ENTRÉE POUR LE BACKEND
# ─────────────────────────────────────────

def get_vetements_recemment_portes(utilisateur, jours: int = 7) -> list:
    """
    Retourne la liste des IDs de vêtements portés dans les N derniers jours.
    Seuls les vêtements avec last_worn renseigné sont exclus (port réel confirmé).

    Returns:
        List[int] des vetement_ids
    """
    date_limite = timezone.now() - timedelta(days=jours)
    return list(
        Vetement.objects.filter(
            utilisateur=utilisateur,
            last_worn__gte=date_limite,
        ).values_list('id', flat=True)
    )


def marquer_tenue_portee(tenue):
    """
    Marque une tenue comme portée aujourd'hui.
    À appeler quand l'utilisateur note/confirme port de la tenue.

    Args:
        tenue: instance Tenue
    """
    if not tenue.haut and not tenue.bas:
        return
    now = timezone.now()
    for vetement in (tenue.haut, tenue.bas, tenue.accessoire):
        if vetement:
            vetement.is_worn = True
            vetement.last_worn = now
            vetement.save(update_fields=['is_worn', 'last_worn'])
