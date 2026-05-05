import heapq
import math
from collections import defaultdict
from wardrobe.models import Vetement
from outfits.models import Tenue
from outfits.services.base import (
    calculer_score_baseline,
    _score_compatibilite_couleur,
    sauvegarder_tenue
)


# ─────────────────────────────────────────
#  CONSTANTES OPTIMISATION
# ─────────────────────────────────────────

# Poids par humeur — influence le scoring final
POIDS_HUMEUR = {
    'heureuse':  {'couleur': 0.40, 'style': 0.35, 'saison': 0.25},
    'triste':    {'couleur': 0.20, 'style': 0.50, 'saison': 0.30},
    'enervee':   {'couleur': 0.30, 'style': 0.45, 'saison': 0.25},
    'calme':     {'couleur': 0.35, 'style': 0.40, 'saison': 0.25},
    'excitee':   {'couleur': 0.45, 'style': 0.30, 'saison': 0.25},
    'neutre':    {'couleur': 0.33, 'style': 0.34, 'saison': 0.33},
}

# Poids par condition météo
POIDS_METEO = {
    'ensoleille':  {'ETE': 1.2,  'HIVER': 0.7, 'PRINTEMPS': 1.0, 'AUTOMNE': 0.9},
    'pluvieux':    {'ETE': 0.8,  'HIVER': 1.1, 'PRINTEMPS': 0.9, 'AUTOMNE': 1.0},
    'nuageux':     {'ETE': 0.9,  'HIVER': 1.0, 'PRINTEMPS': 1.0, 'AUTOMNE': 1.0},
    'chaud':       {'ETE': 1.3,  'HIVER': 0.5, 'PRINTEMPS': 0.9, 'AUTOMNE': 0.8},
    'froid':       {'ETE': 0.5,  'HIVER': 1.3, 'PRINTEMPS': 0.8, 'AUTOMNE': 1.1},
}

# Styles recommandés par humeur
STYLE_PAR_HUMEUR = {
    'heureuse':  ['CASUAL', 'SOIREE'],
    'triste':    ['CASUAL', 'TRADITIONNEL'],
    'enervee':   ['SPORT', 'CASUAL'],
    'calme':     ['FORMEL', 'TRADITIONNEL'],
    'excitee':   ['SOIREE', 'CASUAL'],
    'neutre':    ['CASUAL', 'FORMEL', 'SPORT', 'TRADITIONNEL', 'SOIREE'],
}


# ─────────────────────────────────────────
#  GRAPHE DE COMPATIBILITÉ COULEURS
# ─────────────────────────────────────────

class GrapheCompatibiliteCouleurs:
    """
    Modélise les compatibilités entre couleurs comme un graphe pondéré.

    Structure : liste d'adjacence (dict de dict)
    Utilisation : parcours BFS/DFS pour trouver des palettes cohérentes
    Complexité espace : O(V + E) où V = couleurs, E = compatibilités

    Pourquoi un graphe ?
    Une table de hachage simple (baseline) ne capture pas les
    compatibilités transitives. Ex : blanc→marine→gris est une
    palette cohérente qu'un graphe permet de détecter.
    """

    def __init__(self):
        # Liste d'adjacence : couleur → {couleur_voisine: poids}
        self.adjacence = defaultdict(dict)
        self._construire_graphe()

    def _construire_graphe(self):
        """Construit le graphe de compatibilité couleur."""
        compatibilites = [
            ('#000080', '#FFFFFF', 0.95),  # marine / blanc
            ('#000080', '#F5F5DC', 0.90),  # marine / beige
            ('#000080', '#C0C0C0', 0.85),  # marine / gris
            ('#000080', '#FFD700', 0.80),  # marine / or
            ('#FFFFFF', '#000000', 0.95),  # blanc / noir
            ('#FFFFFF', '#8B0000', 0.88),  # blanc / bordeaux
            ('#FFFFFF', '#2F4F4F', 0.82),  # blanc / vert foncé
            ('#000000', '#FF0000', 0.85),  # noir / rouge
            ('#000000', '#FFD700', 0.88),  # noir / or
            ('#000000', '#C0C0C0', 0.90),  # noir / argent
            ('#F5F5DC', '#8B4513', 0.87),  # beige / marron
            ('#F5F5DC', '#2F4F4F', 0.83),  # beige / vert foncé
            ('#FF0000', '#F5F5DC', 0.80),  # rouge / beige
        ]
        for c1, c2, poids in compatibilites:
            self.adjacence[c1][c2] = poids
            self.adjacence[c2][c1] = poids  # graphe non orienté

    def score_compatibilite(self, hex1: str, hex2: str) -> float:
        """
        Score direct entre deux couleurs.
        Complexité : O(1) accès liste d'adjacence.
        """
        if not hex1 or not hex2:
            return 0.5
        h1 = hex1.upper()
        h2 = hex2.upper()
        return self.adjacence.get(h1, {}).get(h2, 0.5)

    def palette_coherente(self, couleurs: list) -> float:
        """
        Évalue la cohérence d'une palette de 2-3 couleurs.
        Parcours de tous les arcs entre les couleurs données.
        Complexité : O(k²) où k = nombre de couleurs (max 3 ici).
        """
        if len(couleurs) < 2:
            return 0.5
        scores = []
        for i in range(len(couleurs)):
            for j in range(i + 1, len(couleurs)):
                s = self.score_compatibilite(couleurs[i], couleurs[j])
                scores.append(s)
        return sum(scores) / len(scores)


# Instance globale — construite une seule fois
_graphe_couleurs = GrapheCompatibiliteCouleurs()


# ─────────────────────────────────────────
#  SCORE OPTIMISÉ — PONDÉRATION DYNAMIQUE
# ─────────────────────────────────────────

def calculer_score_optimise(haut: Vetement, bas: Vetement,
                             accessoire: Vetement = None,
                             humeur: str = 'neutre',
                             condition_meteo: str = None,
                             saison_actuelle: str = None) -> float:
    """
    Calcule le score d'harmonie — ALGORITHME OPTIMISÉ.

    Différences vs baseline :
      - Graphe de compatibilité couleurs (au lieu de table plate)
      - Poids dynamiques selon humeur (au lieu de poids fixes)
      - Coefficient météo multiplicatif
      - Cohérence palette à 3 couleurs (haut + bas + accessoire)
      - Bonus style adapté à l'humeur

    Complexité : O(1) — toutes les opérations sont en temps constant
                 grâce aux structures précalculées.
    """
    poids = POIDS_HUMEUR.get(humeur, POIDS_HUMEUR['neutre'])

    # ── 1. Score couleur via graphe (max 40) ────────────────────
    couleurs = [v for v in [
        haut.couleur_hex,
        bas.couleur_hex,
        accessoire.couleur_hex if accessoire else None
    ] if v]

    score_couleur = _graphe_couleurs.palette_coherente(couleurs) * 40
    score_couleur *= poids['couleur'] / 0.33  # normalisation par rapport au poids neutre

    # ── 2. Score style avec bonus humeur (max 35) ────────────────
    styles_recommandes = STYLE_PAR_HUMEUR.get(humeur, [])
    score_style = 0

    if haut.style and bas.style:
        if haut.style == bas.style:
            score_style += 20
            if haut.style in styles_recommandes:
                score_style += 15  # bonus humeur
        else:
            score_style += 8
    else:
        score_style += 12

    score_style = min(score_style, 35)
    score_style *= poids['style'] / 0.34

    # ── 3. Score saison avec coefficient météo (max 25) ──────────
    score_saison = 0

    if haut.saison == bas.saison:
        score_saison += 20
    elif 'TOUTES_SAISONS' in [haut.saison, bas.saison]:
        score_saison += 15
    else:
        score_saison += 5

    # Coefficient météo multiplicatif
    if condition_meteo and saison_actuelle:
        coeff = POIDS_METEO.get(
            condition_meteo, {}
        ).get(saison_actuelle, 1.0)
        score_saison = min(score_saison * coeff, 25)

    score_saison *= poids['saison'] / 0.33

    score_final = score_couleur + score_style + score_saison
    return round(min(score_final, 100), 2)


# ─────────────────────────────────────────
#  GÉNÉRATION OPTIMISÉE — TAS BINAIRE + ÉLAGAGE
# ─────────────────────────────────────────

def generer_tenues_optimise(utilisateur, saison=None, style=None,
                             humeur='neutre', condition_meteo=None,
                             saison_actuelle=None, top_k=5) -> list:
    """
    Génère les top_k meilleures tenues — ALGORITHME OPTIMISÉ.

    Optimisations vs baseline :
      1. Élagage précoce : on filtre les vêtements dont le style
         ne correspond pas à l'humeur avant de calculer les scores
         → réduit l'espace de recherche

      2. Score optimisé : graphe couleurs + poids dynamiques humeur
         + coefficient météo (plus précis que la baseline)

      3. Même structure tas binaire min O(n² log k) mais sur un
         espace de recherche réduit → plus rapide en pratique

    Complexité : O(m² log k) où m ≤ n (m = vêtements après élagage)
    Mémoire    : O(k)
    """

    styles_ok = STYLE_PAR_HUMEUR.get(humeur, [])

    # ── Récupération avec élagage précoce ───────────────────────
    hauts_qs = Vetement.objects.filter(
        utilisateur=utilisateur,
        categorie='HAUT',
        est_propre=True
    )
    bas_qs = Vetement.objects.filter(
        utilisateur=utilisateur,
        categorie='BAS',
        est_propre=True
    )
    accessoires_qs = Vetement.objects.filter(
        utilisateur=utilisateur,
        categorie='ACCESSOIRE',
        est_propre=True
    )

    # Élagage par saison
    if saison:
        hauts_qs = hauts_qs.filter(saison__in=[saison, 'TOUTES_SAISONS'])
        bas_qs   = bas_qs.filter(saison__in=[saison, 'TOUTES_SAISONS'])

    # Élagage par style adapté à l'humeur (optimisation clé)
    if styles_ok and humeur != 'neutre':
        hauts_qs = hauts_qs.filter(style__in=styles_ok)
        bas_qs   = bas_qs.filter(style__in=styles_ok)

    hauts       = list(hauts_qs)
    bas_list    = list(bas_qs)
    accessoires = list(accessoires_qs) + [None]

    if not hauts or not bas_list:
        return []

    # ── Tas binaire min — top-k ──────────────────────────────────
    tas = []

    for haut in hauts:
        for bas in bas_list:
            for acc in accessoires:
                score = calculer_score_optimise(
                    haut, bas, acc,
                    humeur=humeur,
                    condition_meteo=condition_meteo,
                    saison_actuelle=saison_actuelle
                )
                entree = (score, haut.id, bas.id,
                          acc.id if acc else None,
                          haut, bas, acc)

                if len(tas) < top_k:
                    heapq.heappush(tas, entree)
                elif score > tas[0][0]:
                    heapq.heapreplace(tas, entree)

    resultats = sorted(tas, key=lambda x: x[0], reverse=True)

    return [
        {
            'haut':           r[4],
            'bas':            r[5],
            'accessoire':     r[6],
            'score_harmonie': r[0],
            'algorithme':     'optimise',
        }
        for r in resultats
    ]


# ─────────────────────────────────────────
#  COMPARAISON BASELINE VS OPTIMISÉ
# ─────────────────────────────────────────

def comparer_algorithmes(utilisateur, saison=None, humeur='neutre',
                          condition_meteo=None,
                          saison_actuelle=None, top_k=5) -> dict:
   
    import time

    # ── Baseline ────────────────────────────────────────────────
    from outfits.services.base import generer_tenues_baseline
    t0 = time.perf_counter()
    resultats_base = generer_tenues_baseline(
        utilisateur=utilisateur,
        saison=saison,
        top_k=top_k
    )
    temps_base = time.perf_counter() - t0

    # ── Optimisé ────────────────────────────────────────────────
    t0 = time.perf_counter()
    resultats_opti = generer_tenues_optimise(
        utilisateur=utilisateur,
        saison=saison,
        humeur=humeur,
        condition_meteo=condition_meteo,
        saison_actuelle=saison_actuelle,
        top_k=top_k
    )
    temps_opti = time.perf_counter() - t0

    # ── Métriques ────────────────────────────────────────────────
    score_moy_base = (
        sum(r['score_harmonie'] for r in resultats_base) / len(resultats_base)
        if resultats_base else 0
    )
    score_moy_opti = (
        sum(r['score_harmonie'] for r in resultats_opti) / len(resultats_opti)
        if resultats_opti else 0
    )

    return {
        'baseline': {
            'tenues':        resultats_base,
            'temps_ms':      round(temps_base * 1000, 3),
            'score_moyen':   round(score_moy_base, 2),
            'nb_tenues':     len(resultats_base),
        },
        'optimise': {
            'tenues':        resultats_opti,
            'temps_ms':      round(temps_opti * 1000, 3),
            'score_moyen':   round(score_moy_opti, 2),
            'nb_tenues':     len(resultats_opti),
        },
        'gain_score':    round(score_moy_opti - score_moy_base, 2),
        'gain_temps_ms': round((temps_base - temps_opti) * 1000, 3),
        'humeur':        humeur,
        'meteo':         condition_meteo,
        'saison':        saison,
    }


# ─────────────────────────────────────────
#  POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────

def generer_et_sauvegarder_optimise(utilisateur, saison=None,
                                     humeur='neutre',
                                     condition_meteo=None,
                                     saison_actuelle=None,
                                     top_k=5) -> list:
    """
    Génère et sauvegarde les top_k tenues optimisées.
    Point d'entrée appelé depuis views.py.
    """
    suggestions = generer_tenues_optimise(
        utilisateur=utilisateur,
        saison=saison,
        humeur=humeur,
        condition_meteo=condition_meteo,
        saison_actuelle=saison_actuelle,
        top_k=top_k
    )

    tenues_sauvegardees = []
    for s in suggestions:
        tenue = sauvegarder_tenue(
            utilisateur=utilisateur,
            haut=s['haut'],
            bas=s['bas'],
            accessoire=s['accessoire'],
            score=int(s['score_harmonie'])
        )
        tenues_sauvegardees.append(tenue)

    return tenues_sauvegardees