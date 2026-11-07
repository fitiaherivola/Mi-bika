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

# Poids par état — influence le scoring final
# On garde la clé 'etat' mais on maintient la compatibilité 'humeur'
POIDS_ETAT = {
    # États physiques
    'malade':   {'couleur': 0.20, 'style': 0.55, 'saison': 0.25},
    'fatigue':  {'couleur': 0.25, 'style': 0.50, 'saison': 0.25},
    'forme':    {'couleur': 0.40, 'style': 0.35, 'saison': 0.25},
    'stresse':  {'couleur': 0.25, 'style': 0.50, 'saison': 0.25},
    'detendu':  {'couleur': 0.35, 'style': 0.40, 'saison': 0.25},
    'festif':   {'couleur': 0.45, 'style': 0.30, 'saison': 0.25},
    # État neutre (aucun état sélectionné)
    'neutre':   {'couleur': 0.33, 'style': 0.34, 'saison': 0.33},
}
# Alias pour compatibilité backward
POIDS_HUMEUR = POIDS_ETAT

# Poids par condition météo
POIDS_METEO = {
    'ensoleille':  {'ETE': 1.2,  'HIVER': 0.7, 'PRINTEMPS': 1.0, 'AUTOMNE': 0.9},
    'pluvieux':    {'ETE': 0.8,  'HIVER': 1.1, 'PRINTEMPS': 0.9, 'AUTOMNE': 1.0},
    'nuageux':     {'ETE': 0.9,  'HIVER': 1.0, 'PRINTEMPS': 1.0, 'AUTOMNE': 1.0},
    'chaud':       {'ETE': 1.3,  'HIVER': 0.5, 'PRINTEMPS': 0.9, 'AUTOMNE': 0.8},
    'froid':       {'ETE': 0.5,  'HIVER': 1.3, 'PRINTEMPS': 0.8, 'AUTOMNE': 1.1},
}

# ─────────────────────────────────────────
#  LOGIQUE ÉTAT PHYSIQUE → SAISON FORCÉE
# ─────────────────────────────────────────

# Si malade → on force HIVER (vêtements chauds) quelle que soit la météo
# Si fatigué → on force ETE (vêtements légers/confortables)
SAISON_PAR_ETAT = {
    'malade':  'HIVER',   # vêtements chauds, peu importe la météo
    'fatigue': 'ETE',     # vêtements légers et confortables
    'stresse': 'ETE',     # vêtements légers pour se détendre
}

# Styles recommandés par état
STYLE_PAR_HUMEUR = {
    # États physiques
    'malade':  ['CASUAL'],                                     # confort max
    'fatigue': ['CASUAL', 'SPORT'],                            # léger et relax
    'forme':   ['SPORT', 'CASUAL', 'SOIREE'],                  # dynamique
    'stresse': ['CASUAL', 'FORMEL'],                           # sobre et simple
    'detendu': ['CASUAL', 'TRADITIONNEL', 'FORMEL'],           # décontracté
    'festif':  ['SOIREE', 'CASUAL'],                           # festif
    # Neutre = tout autorisé
    'neutre':  ['CASUAL', 'FORMEL', 'SPORT', 'TRADITIONNEL', 'SOIREE'],
}
# Alias pour clarté
STYLE_PAR_ETAT = STYLE_PAR_HUMEUR


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
                             etat='neutre', condition_meteo=None,
                             saison_actuelle=None, top_k=5,
                             ids_exclus: list = None,
                             styles_autorises: list = None,
                             avec_accessoire: bool = True) -> list:
    """
    Génère les top_k meilleures tenues — ALGORITHME OPTIMISÉ.

    Priorité de sélection des styles :
      1. style_prefere de l'utilisateur (priorité absolue)
      2. État physique du jour (malade → chaud, fatigué → léger)
      3. Vêtements hors préférence (en complément)

    Logique état physique :
      - malade  → force saison HIVER (chaud), peu importe météo
      - fatigue → force saison ETE (léger et confortable)

    Args:
        etat: état physique du jour ('malade', 'fatigue', 'neutre', ...)
        ids_exclus: IDs à exclure (anti-répétition)
        styles_autorises: liste de styles acceptés (si contrainte SANTE etc.)
        avec_accessoire: inclure ou non les accessoires

    Complexité : O(m² log k) où m ≤ n (m = vêtements après élagage)
    """
    ids_exclus = set(ids_exclus or [])

    # ── Saison forcée par état physique ───────────────────────────
    # malade → HIVER (chaud), fatigue/stresse → ETE (léger)
    # Cela SURPASSE la météo réelle
    saison_effective = SAISON_PAR_ETAT.get(etat, saison)

    # ── Style de préférence de l'utilisateur (priorité 1) ────────
    style_prefere = getattr(utilisateur, 'style_prefere', None)

    # ── Styles selon état (priorité 2) ───────────────────────────
    styles_par_etat = STYLE_PAR_ETAT.get(etat, STYLE_PAR_ETAT['neutre'])

    # ── Construction de la liste ordonnée de styles ───────────────
    # La logique : on génère d'abord avec le style_prefere, puis avec
    # les styles de l'état, puis tous les styles (pour remplir top_k)
    if styles_autorises is not None:
        # Contrainte externe (ex: SANTE) → elle prime sur tout
        styles_ok_pref = styles_autorises
        styles_ok_all  = styles_autorises
    else:
        if style_prefere:
            # Style préféré prend la priorité absolue dans la sélection
            styles_ok_pref = [style_prefere]
            # Ensuite les styles de l'état (sans dupliquer)
            styles_ok_etat = [s for s in styles_par_etat if s != style_prefere]
            # Enfin tous les autres styles de la garde-robe
            tous_les_styles = ['CASUAL', 'FORMEL', 'SPORT', 'TRADITIONNEL', 'SOIREE']
            styles_ok_all = (
                styles_ok_pref
                + styles_ok_etat
                + [s for s in tous_les_styles
                   if s not in styles_ok_pref and s not in styles_ok_etat]
            )
        else:
            styles_ok_pref = styles_par_etat
            styles_ok_all  = styles_par_etat

    # ── Récupération avec élagage ──────────────────────────────────
    hauts_qs = Vetement.objects.filter(
        utilisateur=utilisateur,
        categorie='HAUT',
        est_propre=True
    ).exclude(id__in=ids_exclus)

    bas_qs = Vetement.objects.filter(
        utilisateur=utilisateur,
        categorie='BAS',
        est_propre=True
    ).exclude(id__in=ids_exclus)

    accessoires_qs = Vetement.objects.filter(
        utilisateur=utilisateur,
        categorie='ACCESSOIRE',
        est_propre=True
    ).exclude(id__in=ids_exclus)

    # Élagage par saison (effective = peut être forcée par état)
    if saison_effective:
        hauts_qs = hauts_qs.filter(saison__in=[saison_effective, 'TOUTES_SAISONS'])
        bas_qs   = bas_qs.filter(saison__in=[saison_effective, 'TOUTES_SAISONS'])

    # ── Phase 1 : style préféré uniquement ───────────────────────
    hauts_pref = list(hauts_qs.filter(style__in=styles_ok_pref))
    bas_pref   = list(bas_qs.filter(style__in=styles_ok_pref))

    # ── Phase 2 : tous les styles (pour compléter si top_k non atteint) ─
    hauts_all  = list(hauts_qs.filter(style__in=styles_ok_all))
    bas_all    = list(bas_qs.filter(style__in=styles_ok_all))

    accessoires = list(accessoires_qs) if avec_accessoire else []

    # Style préféré (ex. TRADITIONNEL) sans pièces correspondantes → garde-robe en priorité
    garde_robe_seule = (
        style_prefere
        and styles_autorises is None
        and (not hauts_pref or not bas_pref)
    )

    # Si pas de vêtements selon le style préféré → on prend tout
    hauts    = hauts_pref if hauts_pref else hauts_all
    bas_list = bas_pref   if bas_pref   else bas_all

    # Styles toujours filtrés
    styles_ok = styles_ok_all

    if not hauts or not bas_list:
        return []

    # Helper pour scorer les combinaisons
    def _get_combinaisons_scorees(hauts_src, bas_src, style_source):
        combos = []
        for haut in hauts_src:
            for bas in bas_src:
                accs = accessoires + [None] if avec_accessoire else [None]
                for acc in accs:
                    score = calculer_score_optimise(
                        haut, bas, acc,
                        humeur=etat,
                        condition_meteo=condition_meteo,
                        saison_actuelle=saison_actuelle
                    )
                    combos.append({
                        'haut': haut,
                        'bas': bas,
                        'accessoire': acc,
                        'score_harmonie': score,
                        'algorithme': 'optimise',
                        'style_source': style_source,
                    })
        return combos

    if garde_robe_seule:
        hauts_gr = list(hauts_qs)
        bas_gr   = list(bas_qs)
        if not hauts_gr or not bas_gr:
            return []
        all_combos = _get_combinaisons_scorees(hauts_gr, bas_gr, 'garde_robe')
        all_combos.sort(key=lambda x: x['score_harmonie'], reverse=True)
    else:
        hauts_used   = hauts_pref if hauts_pref else hauts
        bas_used     = bas_pref   if bas_pref   else bas_list
        hauts_autres = [h for h in hauts_all if h not in hauts_used]
        bas_autres   = [b for b in bas_all   if b not in bas_used]

        pref_combos = _get_combinaisons_scorees(hauts_used, bas_used, 'preference')
        pref_combos.sort(key=lambda x: x['score_harmonie'], reverse=True)

        autres_combos = []
        if hauts_autres or bas_autres:
            hauts_mix = hauts_autres if hauts_autres else hauts_used
            bas_mix   = bas_autres   if bas_autres   else bas_used
            autres_combos = _get_combinaisons_scorees(hauts_mix, bas_mix, 'garde_robe')
            autres_combos.sort(key=lambda x: x['score_harmonie'], reverse=True)

        all_combos = pref_combos + autres_combos

    # Sélectionner les top_k tenues avec (haut, bas) uniques
    resultats = []
    seen_pairs = set()
    for combo in all_combos:
        pair = (combo['haut'].id, combo['bas'].id)
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            resultats.append(combo)
            if len(resultats) >= top_k:
                break

    return resultats


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
                                     etat='neutre',
                                     condition_meteo=None,
                                     saison_actuelle=None,
                                     top_k=5,
                                     ids_exclus: list = None,
                                     styles_autorises: list = None,
                                     avec_accessoire: bool = True) -> list:
    """
    Génère et sauvegarde les top_k tenues optimisées.
    Point d'entrée appelé depuis views.py.

    Priorité de génération :
      1. Style préféré de l'utilisateur (style_prefere)
      2. État physique du jour (malade → HIVER, fatigué → ETE)
      3. Autres vêtements de la garde-robe (en complément)

    Args:
        etat: état physique ('malade', 'fatigue', 'neutre', ...)
        styles_autorises: liste de styles acceptés (contrainte externe)
        avec_accessoire: inclure les accessoires
    """
    suggestions = generer_tenues_optimise(
        utilisateur=utilisateur,
        saison=saison,
        etat=etat,
        condition_meteo=condition_meteo,
        saison_actuelle=saison_actuelle,
        top_k=top_k,
        ids_exclus=ids_exclus,
        styles_autorises=styles_autorises,
        avec_accessoire=avec_accessoire,
    )

    tenues_sauvegardees = []
    for s in suggestions:
        tenue = sauvegarder_tenue(
            utilisateur=utilisateur,
            haut=s['haut'],
            bas=s['bas'],
            accessoire=s['accessoire'],
            score=int(s['score_harmonie']),
            algorithme=s.get('algorithme', 'optimise'),
        )
        tenues_sauvegardees.append(tenue)

    return tenues_sauvegardees