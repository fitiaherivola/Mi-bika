import heapq
from wardrobe.models import Vetement
from outfits.models import Tenue


# ─────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────

COMPATIBILITE_COULEURS = {
    # Bleu marine
    '#000080': ['#FFFFFF', '#F5F5DC', '#C0C0C0', '#FFD700'],
    # Blanc
    '#FFFFFF': ['#000000', '#000080', '#8B0000', '#2F4F4F'],
    # Noir
    '#000000': ['#FFFFFF', '#FF0000', '#FFD700', '#C0C0C0'],
    # Beige
    '#F5F5DC': ['#8B4513', '#2F4F4F', '#000080', '#696969'],
    # Rouge
    '#FF0000': ['#000000', '#FFFFFF', '#F5F5DC'],
}

STYLE_SAISON_SCORE = {
    ('CASUAL',       'ETE'):         90,
    ('CASUAL',       'TOUTES_SAISONS'): 85,
    ('SPORT',        'ETE'):         88,
    ('SPORT',        'TOUTES_SAISONS'): 82,
    ('FORMEL',       'TOUTES_SAISONS'): 80,
    ('TRADITIONNEL', 'TOUTES_SAISONS'): 85,
    ('SOIREE',       'TOUTES_SAISONS'): 78,
}


# ─────────────────────────────────────────
#  UTILITAIRES COULEUR
# ─────────────────────────────────────────

def _normaliser_hex(couleur: str) -> str:
    """Normalise une couleur hex en majuscules."""
    if not couleur:
        return ''
    return couleur.upper().strip()


def _score_compatibilite_couleur(hex1: str, hex2: str) -> int:
    """
    Vérifie la compatibilité entre deux couleurs.
    Retourne un score : 30 (compatible), 15 (neutre), 0 (incompatible).
    Structure utilisée : table de hachage (dict Python).
    Complexité : O(1) accès amorti.
    """
    if not hex1 or not hex2:
        return 15 

    h1 = _normaliser_hex(hex1)
    h2 = _normaliser_hex(hex2)

    compatibles = COMPATIBILITE_COULEURS.get(h1, [])
    if h2 in compatibles:
        return 30
    compatibles2 = COMPATIBILITE_COULEURS.get(h2, [])
    if h1 in compatibles2:
        return 30
    if h1 == h2:
        return 10 
    return 15  


# ─────────────────────────────────────────
#  CALCUL SCORE HARMONIE (BASELINE)
# ─────────────────────────────────────────

def calculer_score_baseline(haut: Vetement, bas: Vetement,
                             accessoire: Vetement = None) -> int:
    """
    Calcule le score d'harmonie d'une tenue — ALGORITHME BASELINE.

    Logique naïve : somme pondérée de critères simples.
    Pas d'apprentissage, pas d'optimisation — sert de référence
    pour la comparaison avec l'algorithme optimisé.

    Critères :
      - Compatibilité couleur haut/bas        : 0-30 pts
      - Cohérence de style haut/bas           : 0-25 pts
      - Cohérence de saison                   : 0-20 pts
      - Compatibilité couleur haut/accessoire : 0-15 pts
      - Propreté des vêtements                : 0-10 pts

    Complexité : O(1) — aucune boucle, accès directs.
    """
    score = 0


    score += _score_compatibilite_couleur(haut.couleur_hex, bas.couleur_hex)

    if haut.style and bas.style:
        if haut.style == bas.style:
            score += 25
        else:
            score += 10 
    else:
        score += 15 

    if haut.saison == bas.saison:
        score += 20
    elif haut.saison == 'TOUTES_SAISONS' or bas.saison == 'TOUTES_SAISONS':
        score += 15
    else:
        score += 5 

  
    if accessoire:
        score += _score_compatibilite_couleur(
            haut.couleur_hex, accessoire.couleur_hex
        )
    else:
        score += 8  

    propres = sum([haut.est_propre, bas.est_propre,
                   accessoire.est_propre if accessoire else True])
    score += propres * 3 

    return min(score, 100)


# ─────────────────────────────────────────
#  GÉNÉRATION BASELINE — TOP-K avec TAS BINAIRE
# ─────────────────────────────────────────

def generer_tenues_baseline(utilisateur, saison=None, style=None,
                             humeur=None, top_k=5) -> list:
    """
    Génère les top_k meilleures tenues pour un utilisateur.

    ALGORITHME BASELINE :
      1. Récupère tous les hauts et bas propres de l'utilisateur
      2. Calcule le score de chaque combinaison haut × bas
      3. Maintient un tas binaire min de taille k pour garder les top-k
         sans trier toute la liste

    Structure : Tas binaire min (heapq Python)
    Complexité : O(n² log k) où n = nb vêtements, k = top_k
    Mémoire    : O(k) — on ne garde que k tenues en mémoire

    Args:
        utilisateur : instance Utilisateur
        saison      : filtre optionnel ('ETE', 'HIVER'...)
        style       : filtre optionnel ('CASUAL', 'FORMEL'...)
        humeur      : non utilisé en baseline (réservé pour optimisé)
        top_k       : nombre de tenues à retourner

    Returns:
        Liste de dicts triés par score décroissant
    """

    # ── Récupération des vêtements ──────────────────────────────
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

    # Filtres optionnels
    if saison:
        hauts_qs = hauts_qs.filter(saison__in=[saison, 'TOUTES_SAISONS'])
        bas_qs   = bas_qs.filter(saison__in=[saison, 'TOUTES_SAISONS'])
    if style:
        hauts_qs = hauts_qs.filter(style=style)
        bas_qs   = bas_qs.filter(style=style)

    hauts       = list(hauts_qs)
    bas_list    = list(bas_qs)
    accessoires = list(accessoires_qs) + [None]  

    if not hauts or not bas_list:
        return []  # garde-robe insuffisante

   
    tas = []

    for haut in hauts:
        for bas in bas_list:
            for acc in accessoires:
                score = calculer_score_baseline(haut, bas, acc)

                if len(tas) < top_k:
                    heapq.heappush(tas, (score, haut.id, bas.id,
                                         acc.id if acc else None,
                                         haut, bas, acc))
                elif score > tas[0][0]:
                    # Remplace le moins bon si on trouve mieux
                    heapq.heapreplace(tas, (score, haut.id, bas.id,
                                             acc.id if acc else None,
                                             haut, bas, acc))

    # ── Tri final décroissant ────────────────────────────────────
    resultats = sorted(tas, key=lambda x: x[0], reverse=True)

    return [
        {
            'haut':          r[4],
            'bas':           r[5],
            'accessoire':    r[6],
            'score_harmonie': r[0],
            'algorithme':    'baseline',
        }
        for r in resultats
    ]


# ─────────────────────────────────────────
#  SAUVEGARDE EN BASE
# ─────────────────────────────────────────

def sauvegarder_tenue(utilisateur, haut: Vetement, bas: Vetement,
                       accessoire: Vetement = None,
                       score: int = 0) -> Tenue:
    
    tenue = Tenue.objects.create(
        utilisateur=utilisateur,
        haut=haut,
        bas=bas,
        accessoire=accessoire,
        score_harmonie=score
    )
    return tenue


# ─────────────────────────────────────────
#  POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────

def generer_et_sauvegarder_baseline(utilisateur, saison=None,
                                     style=None, top_k=5) -> list:
    """
    Génère et sauvegarde les top_k tenues en base.
    Point d'entrée appelé depuis views.py.

    Returns:
        Liste des instances Tenue sauvegardées
    """
    suggestions = generer_tenues_baseline(
        utilisateur=utilisateur,
        saison=saison,
        style=style,
        top_k=top_k
    )

    tenues_sauvegardees = []
    for s in suggestions:
        tenue = sauvegarder_tenue(
            utilisateur=utilisateur,
            haut=s['haut'],
            bas=s['bas'],
            accessoire=s['accessoire'],
            score=s['score_harmonie']
        )
        tenues_sauvegardees.append(tenue)

    return tenues_sauvegardees