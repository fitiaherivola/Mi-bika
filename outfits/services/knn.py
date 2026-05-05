import math
from outfits.models import Tenue
from wardrobe.models import Vetement


# ─────────────────────────────────────────
#  VECTORISATION D'UNE TENUE
#  Convertit une tenue en vecteur numérique
#  pour pouvoir calculer des distances
# ─────────────────────────────────────────

CATEGORIES = ['HAUT', 'BAS', 'ACCESSOIRE']
STYLES      = ['CASUAL', 'FORMEL', 'SPORT', 'TRADITIONNEL', 'SOIREE']
SAISONS     = ['ETE', 'HIVER', 'PRINTEMPS', 'AUTOMNE', 'TOUTES_SAISONS']


def _encoder_one_hot(valeur: str, liste: list) -> list:
    """
    Encodage one-hot d'une valeur catégorielle.
    Ex : 'CASUAL' dans STYLES → [1, 0, 0, 0, 0]
    Complexité : O(k) où k = taille de la liste.
    """
    return [1 if valeur == item else 0 for item in liste]


def _hex_vers_rgb(hex_couleur: str) -> tuple:
    """
    Convertit une couleur hex en tuple RGB normalisé [0, 1].
    Ex : '#FF0000' → (1.0, 0.0, 0.0)
    Retourne (0.5, 0.5, 0.5) si couleur inconnue.
    """
    if not hex_couleur or len(hex_couleur) != 7:
        return (0.5, 0.5, 0.5)
    try:
        h = hex_couleur.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r / 255.0, g / 255.0, b / 255.0)
    except ValueError:
        return (0.5, 0.5, 0.5)


def vectoriser_tenue(tenue: Tenue) -> list:
    """
    Convertit une tenue en vecteur numérique pour le k-NN.

    Vecteur final (dimension fixe) :
      [0-4]   style haut        (one-hot, 5 dims)
      [5-9]   style bas         (one-hot, 5 dims)
      [10-14] saison haut       (one-hot, 5 dims)
      [15-19] saison bas        (one-hot, 5 dims)
      [20-22] couleur haut RGB  (3 dims, normalisé)
      [23-25] couleur bas RGB   (3 dims, normalisé)
      [26]    score_harmonie    (normalisé 0-1)
      [27]    a_accessoire      (0 ou 1)

    Dimension totale : 28
    Complexité : O(1) — taille fixe indépendante des données.
    """
    vecteur = []

    # Style haut (5 dims)
    style_haut = tenue.haut.style if tenue.haut else 'CASUAL'
    vecteur += _encoder_one_hot(style_haut, STYLES)

    # Style bas (5 dims)
    style_bas = tenue.bas.style if tenue.bas else 'CASUAL'
    vecteur += _encoder_one_hot(style_bas, STYLES)

    # Saison haut (5 dims)
    saison_haut = tenue.haut.saison if tenue.haut else 'TOUTES_SAISONS'
    vecteur += _encoder_one_hot(saison_haut, SAISONS)

    # Saison bas (5 dims)
    saison_bas = tenue.bas.saison if tenue.bas else 'TOUTES_SAISONS'
    vecteur += _encoder_one_hot(saison_bas, SAISONS)

    # Couleur haut RGB normalisée (3 dims)
    couleur_haut = tenue.haut.couleur_hex if tenue.haut else None
    vecteur += list(_hex_vers_rgb(couleur_haut))

    # Couleur bas RGB normalisée (3 dims)
    couleur_bas = tenue.bas.couleur_hex if tenue.bas else None
    vecteur += list(_hex_vers_rgb(couleur_bas))

    # Score harmonie normalisé (1 dim)
    vecteur.append(tenue.score_harmonie / 100.0)

    # A un accessoire (1 dim)
    vecteur.append(1.0 if tenue.accessoire else 0.0)

    return vecteur  # longueur = 28


# ─────────────────────────────────────────
#  DISTANCE EUCLIDIENNE
#  Mesure la similarité entre deux vecteurs
# ─────────────────────────────────────────

def distance_euclidienne(v1: list, v2: list) -> float:
    """
    Calcule la distance euclidienne entre deux vecteurs.

    d(v1, v2) = sqrt(Σ (v1i - v2i)²)

    Plus la distance est petite → plus les tenues sont similaires.
    Complexité : O(d) où d = dimension du vecteur (28 ici, donc O(1)).
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


# ─────────────────────────────────────────
#  ALGORITHME K-NN
#  Trouve les k tenues les plus similaires
# ─────────────────────────────────────────

class KNNTenues:
    """
    Classificateur k-NN pour recommandation de tenues.

    Principe :
      Pour une tenue requête Q, trouver les k tenues
      de l'historique les plus proches selon la distance
      euclidienne dans l'espace des vecteurs de tenues.

    Pourquoi k-NN ?
      - Pas d'entraînement préalable (lazy learning)
      - Interprétable : on peut expliquer pourquoi une tenue
        est recommandée (même style, même couleur...)
      - Adapté à une petite garde-robe (pas besoin de big data)

    Complexité recherche : O(n × d) où n = nb tenues historique,
                           d = dimension vecteur (28, donc O(n))
    Complexité espace    : O(n × d) pour stocker les vecteurs
    """

    def __init__(self, k: int = 3):
        self.k         = k
        self.historique = []   # liste de (vecteur, tenue, score)

    def entrainer(self, utilisateur):
        """
        Charge l'historique des tenues de l'utilisateur.
        Vectorise chaque tenue et la stocke en mémoire.

        Complexité : O(n × d) où n = nb tenues historique.
        """
        tenues = Tenue.objects.filter(
            utilisateur=utilisateur,
            score_harmonie__gte=50   # on garde seulement les bonnes tenues
        ).select_related('haut', 'bas', 'accessoire')

        self.historique = []
        for tenue in tenues:
            if tenue.haut and tenue.bas:  # tenue complète uniquement
                vecteur = vectoriser_tenue(tenue)
                self.historique.append({
                    'vecteur': vecteur,
                    'tenue':   tenue,
                    'score':   tenue.score_harmonie,
                })

    def recommander(self, tenue_requete: Tenue) -> list:
        """
        Retourne les k tenues les plus similaires à tenue_requete.

        Algorithme :
          1. Vectorise la tenue requête
          2. Calcule la distance euclidienne avec chaque tenue historique
          3. Trie par distance croissante
          4. Retourne les k plus proches

        Complexité : O(n log n) — calcul distances O(n) + tri O(n log n)

        Returns:
            Liste de dicts triés par similarité décroissante
        """
        if not self.historique:
            return []

        if not tenue_requete.haut or not tenue_requete.bas:
            return []

        vecteur_requete = vectoriser_tenue(tenue_requete)

        # Calcul des distances pour tous les voisins
        distances = []
        for item in self.historique:
            if item['tenue'].id == tenue_requete.id:
                continue  # on exclut la tenue elle-même
            dist = distance_euclidienne(vecteur_requete, item['vecteur'])
            distances.append({
                'tenue':      item['tenue'],
                'distance':   round(dist, 4),
                'score':      item['score'],
                'similarite': round((1 / (1 + dist)) * 100, 2),
            })

        # Tri par distance croissante → les plus similaires en premier
        distances.sort(key=lambda x: x['distance'])

        return distances[:self.k]


# ─────────────────────────────────────────
#  POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────

def recommander_tenues_similaires(utilisateur,
                                   tenue_reference: Tenue,
                                   k: int = 3) -> list:
    """
    Recommande k tenues similaires à une tenue de référence.
    Point d'entrée appelé depuis views.py.

    Args:
        utilisateur     : instance Utilisateur
        tenue_reference : la tenue dont on cherche des similaires
        k               : nombre de recommandations

    Returns:
        Liste de dicts avec tenue + distance + similarité %
    """
    knn = KNNTenues(k=k)
    knn.entrainer(utilisateur)
    return knn.recommander(tenue_reference)


def recommander_depuis_humeur(utilisateur, humeur: str,
                               k: int = 3) -> list:
    """
    Recommande k tenues depuis l'historique selon l'humeur.

    Logique :
      1. Cherche dans l'historique une tenue dont le style
         correspond à l'humeur
      2. Utilise cette tenue comme référence pour le k-NN

    Args:
        utilisateur : instance Utilisateur
        humeur      : ex 'heureuse', 'calme', 'sport'...
        k           : nombre de recommandations
    """
    from outfits.services.optimise import STYLE_PAR_HUMEUR

    styles_cibles = STYLE_PAR_HUMEUR.get(humeur, [])

    # Cherche une tenue de référence dans l'historique
    tenue_ref = None
    for style in styles_cibles:
        tenue_ref = Tenue.objects.filter(
            utilisateur=utilisateur,
            score_harmonie__gte=60,
            haut__style=style
        ).select_related('haut', 'bas', 'accessoire').first()
        if tenue_ref:
            break

    if not tenue_ref:
        return []

    return recommander_tenues_similaires(utilisateur, tenue_ref, k=k)


# ─────────────────────────────────────────
#  MESURE POUR DOSSIER ALGORITHMIQUE
# ─────────────────────────────────────────

def comparer_knn_vs_baseline(utilisateur, k: int = 3) -> dict:
    """
    Compare k-NN vs baseline sur le score moyen des recommandations.
    Génère les métriques pour ton tableau comparatif.
    """
    import time
    from outfits.services.base import generer_tenues_baseline

    # Baseline
    t0 = time.perf_counter()
    res_base = generer_tenues_baseline(utilisateur, top_k=k)
    temps_base = time.perf_counter() - t0

    # k-NN — utilise la meilleure tenue historique comme référence
    t0 = time.perf_counter()
    tenue_ref = Tenue.objects.filter(
        utilisateur=utilisateur,
        score_harmonie__gte=50
    ).order_by('-score_harmonie').first()

    res_knn = []
    if tenue_ref:
        res_knn = recommander_tenues_similaires(utilisateur, tenue_ref, k=k)
    temps_knn = time.perf_counter() - t0

    score_base = (
        sum(r['score_harmonie'] for r in res_base) / len(res_base)
        if res_base else 0
    )
    score_knn = (
        sum(r['score'] for r in res_knn) / len(res_knn)
        if res_knn else 0
    )

    return {
        'baseline': {
            'temps_ms':    round(temps_base * 1000, 3),
            'score_moyen': round(score_base, 2),
            'methode':     'combinaisons haut×bas O(n²)',
        },
        'knn': {
            'temps_ms':    round(temps_knn * 1000, 3),
            'score_moyen': round(score_knn, 2),
            'methode':     f'k={k} voisins O(n×d)',
        },
        'gain_score': round(score_knn - score_base, 2),
    }