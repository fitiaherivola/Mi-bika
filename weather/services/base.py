from datetime import date, timedelta
from weather.models import Meteo


# ─────────────────────────────────────────
#  RÉCUPÉRATION MÉTÉO
# ─────────────────────────────────────────

def get_meteo_du_jour(ville: str) -> Meteo | None:
    """
    Retourne la météo du jour pour une ville.
    Complexité : O(1) — accès indexé par ville + date.
    """
    return Meteo.objects.filter(
        ville__iexact=ville,
        date_prediction=date.today()
    ).first()


def get_derniere_meteo(ville: str) -> Meteo | None:
    """Dernière entrée en base pour une ville (même si date ≠ aujourd'hui)."""
    return Meteo.objects.filter(ville__iexact=ville).order_by('-date_prediction').first()


def meteo_fallback_dict(ville: str) -> dict:
    """Valeurs par défaut pour Antananarivo / Madagascar — réponse instantanée."""
    return {
        'id': None,
        'ville': ville,
        'temperature': 24.0,
        'condition': 'ensoleille',
        'date_prediction': date.today().isoformat(),
        'saison_estimee': 'ETE',
        'source': 'defaut',
        'message': 'Estimation locale (synchronisez plus tard si besoin)',
    }


def get_meteo_par_ville(ville: str, jours: int = 7) -> list:
    """
    Retourne l'historique météo d'une ville sur N jours.
    Complexité : O(n) où n = nb entrées sur la période.
    """
    date_debut = date.today() - timedelta(days=jours)
    return list(
        Meteo.objects.filter(
            ville__iexact=ville,
            date_prediction__gte=date_debut
        ).order_by('-date_prediction')
    )


def get_meteo_par_id(meteo_id: int) -> Meteo | None:
    """
    Retourne une météo par son id.
    Complexité : O(1) — accès par clé primaire.
    """
    try:
        return Meteo.objects.get(id=meteo_id)
    except Meteo.DoesNotExist:
        return None


def enregistrer_meteo(ville: str, temperature: float,
                       condition: str,
                       date_prediction: date = None) -> Meteo:
    """
    Enregistre ou met à jour une météo pour une ville et une date.
    Utilise get_or_create pour éviter les doublons.
    Complexité : O(1).
    """
    meteo, _ = Meteo.objects.update_or_create(
        ville=ville,
        date_prediction=date_prediction or date.today(),
        defaults={
            'temperature': temperature,
            'condition':   condition,
        }
    )
    return meteo


# ─────────────────────────────────────────
#  CONVERSION MÉTÉO → CONTRAINTES TENUE
# ─────────────────────────────────────────

def meteo_vers_contraintes(meteo: Meteo) -> dict:
    """
    Convertit une météo en paramètres utilisables par
    outfits/services/optimise.py pour la génération de tenues.

    Returns:
        {
            'condition_meteo' : str  — ex: 'ensoleille'
            'saison_actuelle' : str  — ex: 'ETE'
            'temperature'     : float
            'conseil'         : str  — message affiché à l'utilisateur
        }
    """
    saison = meteo.saison_estimee()
    t      = meteo.temperature

    # Conseil vestimentaire selon température
    if t >= 30:
        conseil = "Très chaud — privilégiez des vêtements légers et aérés."
    elif t >= 22:
        conseil = "Chaud — une tenue légère est idéale."
    elif t >= 15:
        conseil = "Doux — une couche légère suffit."
    elif t >= 8:
        conseil = "Frais — pensez à une veste ou un pull."
    else:
        conseil = "Froid — habillez-vous chaudement."

    return {
        'condition_meteo': meteo.condition,
        'saison_actuelle': saison,
        'temperature':     t,
        'conseil':         conseil,
    }


def contraintes_depuis_ville(ville: str) -> dict | None:
    """
    Récupère la météo du jour d'une ville et retourne
    directement les contraintes pour la génération de tenues.
    Point d'entrée principal utilisé par views.py.

    Returns:
        Dict de contraintes ou None si météo introuvable.
    """
    meteo = get_meteo_du_jour(ville)
    if not meteo:
        return None
    return meteo_vers_contraintes(meteo)


# ─────────────────────────────────────────
#  STATISTIQUES
# ─────────────────────────────────────────

def stats_meteo(ville: str, jours: int = 7) -> dict:
    """
    Calcule des statistiques météo sur N jours pour une ville.
    Utile pour les logs de démo et le dashboard.
    Complexité : O(n) — un seul parcours.
    """
    historique = get_meteo_par_ville(ville, jours)

    if not historique:
        return {
            'ville':           ville,
            'nb_jours':        0,
            'temp_moyenne':    None,
            'temp_min':        None,
            'temp_max':        None,
            'condition_dominante': None,
        }

    temperatures  = [m.temperature for m in historique]
    conditions    = [m.condition for m in historique]

    # Condition dominante — table de hachage O(n)
    compteur = {}
    for c in conditions:
        compteur[c] = compteur.get(c, 0) + 1
    condition_dominante = max(compteur, key=compteur.get)

    return {
        'ville':               ville,
        'nb_jours':            len(historique),
        'temp_moyenne':        round(sum(temperatures) / len(temperatures), 1),
        'temp_min':            min(temperatures),
        'temp_max':            max(temperatures),
        'condition_dominante': condition_dominante,
        'saison_estimee':      historique[0].saison_estimee(),
    }