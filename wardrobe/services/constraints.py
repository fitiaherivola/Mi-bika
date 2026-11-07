"""
Service d'application des contraintes personnelles utilisateur.
"""

from datetime import timedelta
from django.utils import timezone
from wardrobe.models import Contrainte
from .sliding_window import get_vetements_recemment_portes


def get_contraintes_actives(utilisateur) -> list:
    """
    Retourne les contraintes actives de l'utilisateur
    (activées dans les 7 derniers jours, triées par priorité).
    """
    cutoff = timezone.now().date() - timedelta(days=7)
    return Contrainte.objects.filter(
        utilisateur=utilisateur,
        date_activation__gte=cutoff
    ).order_by('-priorite')  # haute priorité en premier


def appliquer_contraintes(utilisateur,
                          saison: str = None,
                          style: str = None,
                          avec_accessoire: bool = True) -> dict:
    """
    Calcule les paramètres de génération à partir des contraintes actives.

    Returns:
        {
          'saison':          str | None,   # override saison si SANTE+malade hiver?
          'styles_autorises': list,        # liste de styles autorisés (si SANTE)
          'avec_accessoire':  bool,        # False si contrainte TEMPS prioritaire
          'ids_exclus':       list,        # IDs à éviter (REPETITION)
        }
    """
    contraintes = get_contraintes_actives(utilisateur)

    # Par défaut
    result = {
        'saison':           saison,
        'styles_autorises': [style] if style else None,
        'avec_accessoire':  avec_accessoire,
        'ids_exclus':       [],
    }

    # Si aucune contrainte → on retourne les paramètres fournis
    if not contraintes:
        return result

    # On traverse les contraintes par priorité décroissante
    for c in contraintes:
        if c.type_contrainte == Contrainte.TypeContrainte.SANTE:
            # SANTE → style confortable (CASUAL) + saison adaptée (si fièvre → HIVER?)
            # On ne connaît pas la température exacte, donc on force CASUAL
            result['styles_autorises'] = ['CASUAL']  # override
            # avec_accessoire = False (moins d'objets)
            result['avec_accessoire'] = False

        elif c.type_contrainte == Contrainte.TypeContrainte.LESSIVE:
            # LESSIVE → s'assurer que est_propre=True (déjà géré dans queryset)
            # Mais on peut forcer exclusion des sales même si est_propare non mis à jour
            # On ne fait rien ici car les querysets filtrent déjà est_propre=True
            pass

        elif c.type_contrainte == Contrainte.TypeContrainte.TEMPS:
            # TEMPS → tenues simples, sans accessoire
            result['avec_accessoire'] = False  # override

        elif c.type_contrainte == Contrainte.TypeContrainte.REPETITION:
            # REPETITION → on active la sliding window pour exclure récents
            # On calcule les IDs récents selon la priorité de la contrainte
            # Plus la priorité est haute, plus la fenêtre est longue?
            jours = 7 * c.priorite  # 7, 14 ou 21 jours selon priorité 1/2/3
            ids_recents = get_vetements_recemment_portes(utilisateur, jours=jours)
            result['ids_exclus'].extend(ids_recents)

    # Nettoyage doublons
    result['ids_exclus'] = list(set(result['ids_exclus']))

    return result


def contrainte_est_active(utilisateur, type_contrainte: str) -> bool:
    """
    Vérifie rapidement si une contrainte donnée est activable.
    """
    cutoff = timezone.now().date() - timedelta(days=7)
    return Contrainte.objects.filter(
        utilisateur=utilisateur,
        type_contrainte=type_contrainte,
        date_activation__gte=cutoff
    ).exists()
