from wardrobe.models import Vetement


# ─────────────────────────────────────────
#  STRUCTURE 1 : TRIE
#  Recherche textuelle optimisée O(m)
#  m = longueur du mot recherché
# ─────────────────────────────────────────

class NoeudTrie:
    """
    Nœud d'un Trie (arbre préfixe).
    Chaque nœud représente un caractère.
    """
    def __init__(self):
        self.enfants   = {}       # dict char → NoeudTrie
        self.est_fin   = False    # True si fin d'un mot
        self.vetements = []       # vêtements associés à ce préfixe


class Trie:
    """
    Arbre préfixe pour recherche textuelle rapide.

    Pourquoi un Trie ?
      - base.py utilise icontains → O(n) scan de toute la table
      - Le Trie permet une recherche par préfixe en O(m)
        où m = longueur du terme recherché, indépendamment de n

    Structure : arbre où chaque arc = un caractère
    Espace    : O(n × m) où n = nb vêtements, m = longueur moyenne des noms
    """

    def __init__(self):
        self.racine = NoeudTrie()

    def inserer(self, mot: str, vetement: Vetement):
        """
        Insère un mot dans le Trie et associe le vêtement.
        Complexité : O(m) où m = len(mot).
        """
        noeud = self.racine
        for char in mot.lower():
            if char not in noeud.enfants:
                noeud.enfants[char] = NoeudTrie()
            noeud = noeud.enfants[char]
            noeud.vetements.append(vetement)
        noeud.est_fin = True

    def rechercher_prefixe(self, prefixe: str) -> list:
        """
        Retourne tous les vêtements dont le nom commence par prefixe.
        Complexité : O(m) pour descendre + O(k) pour collecter
                     k = nb résultats — bien meilleur que O(n) de base.py
        """
        noeud = self.racine
        for char in prefixe.lower():
            if char not in noeud.enfants:
                return []  # préfixe introuvable
            noeud = noeud.enfants[char]
        return noeud.vetements

    def rechercher_exact(self, mot: str) -> list:
        """
        Retourne les vêtements dont le nom correspond exactement.
        Complexité : O(m).
        """
        noeud = self.racine
        for char in mot.lower():
            if char not in noeud.enfants:
                return []
            noeud = noeud.enfants[char]
        return noeud.vetements if noeud.est_fin else []


def construire_trie(utilisateur) -> Trie:
    """
    Construit un Trie à partir de la garde-robe d'un utilisateur.
    Complexité : O(n × m) où n = nb vêtements, m = longueur moyenne des noms.
    """
    trie = Trie()
    vetements = Vetement.objects.filter(utilisateur=utilisateur)
    for v in vetements:
        trie.inserer(v.nom, v)
    return trie


def rechercher_vetements_trie(utilisateur, terme: str) -> list:
    """
    Recherche optimisée par Trie — remplace rechercher_vetements() de base.py.

    Baseline  : icontains → O(n) scan séquentiel
    Optimisé  : Trie       → O(m) indépendant de n

    Args:
        utilisateur : instance Utilisateur
        terme       : préfixe ou mot à rechercher

    Returns:
        Liste de Vetement correspondants (sans doublons)
    """
    if not terme or len(terme.strip()) == 0:
        return []

    trie = construire_trie(utilisateur)
    resultats = trie.rechercher_prefixe(terme.strip())

    # Dédoublonnage en conservant l'ordre
    vus = set()
    uniques = []
    for v in resultats:
        if v.id not in vus:
            vus.add(v.id)
            uniques.append(v)
    return uniques


# ─────────────────────────────────────────
#  STRUCTURE 2 : AVL
#  Tri dynamique des vêtements par score
# ─────────────────────────────────────────

class NoeudAVL:
    """
    Nœud d'un arbre AVL.
    Clé = score du vêtement (0-100), Valeur = Vetement.
    """
    def __init__(self, cle: float, vetement: Vetement):
        self.cle      = cle
        self.vetement = vetement
        self.gauche   = None
        self.droite   = None
        self.hauteur  = 1


class AVL:
    """
    Arbre binaire de recherche auto-équilibré (AVL).

    Pourquoi un AVL ?
      - base.py utilise sorted() → O(n log n) à chaque appel
      - L'AVL maintient le tri dynamiquement :
        insertion O(log n), recherche O(log n)
      - Utile quand la garde-robe change souvent

    Propriété AVL : |hauteur(gauche) - hauteur(droite)| ≤ 1
    Complexité    : O(log n) insertion, recherche, suppression
    """

    def __init__(self):
        self.racine = None

    # ── Utilitaires ──────────────────────────────────────────────

    def _hauteur(self, noeud) -> int:
        return noeud.hauteur if noeud else 0

    def _facteur_equilibre(self, noeud) -> int:
        return self._hauteur(noeud.gauche) - self._hauteur(noeud.droite)

    def _maj_hauteur(self, noeud):
        noeud.hauteur = 1 + max(
            self._hauteur(noeud.gauche),
            self._hauteur(noeud.droite)
        )

    # ── Rotations ────────────────────────────────────────────────

    def _rotation_droite(self, y: NoeudAVL) -> NoeudAVL:
        """Rotation droite pour rééquilibrer. Complexité O(1)."""
        x  = y.gauche
        T2 = x.droite
        x.droite  = y
        y.gauche  = T2
        self._maj_hauteur(y)
        self._maj_hauteur(x)
        return x

    def _rotation_gauche(self, x: NoeudAVL) -> NoeudAVL:
        """Rotation gauche pour rééquilibrer. Complexité O(1)."""
        y  = x.droite
        T2 = y.gauche
        y.gauche  = x
        x.droite  = T2
        self._maj_hauteur(x)
        self._maj_hauteur(y)
        return y

    def _equilibrer(self, noeud: NoeudAVL) -> NoeudAVL:
        """Rééquilibre un nœud si nécessaire."""
        self._maj_hauteur(noeud)
        fe = self._facteur_equilibre(noeud)

        # Cas gauche-gauche
        if fe > 1 and self._facteur_equilibre(noeud.gauche) >= 0:
            return self._rotation_droite(noeud)
        # Cas gauche-droite
        if fe > 1 and self._facteur_equilibre(noeud.gauche) < 0:
            noeud.gauche = self._rotation_gauche(noeud.gauche)
            return self._rotation_droite(noeud)
        # Cas droite-droite
        if fe < -1 and self._facteur_equilibre(noeud.droite) <= 0:
            return self._rotation_gauche(noeud)
        # Cas droite-gauche
        if fe < -1 and self._facteur_equilibre(noeud.droite) > 0:
            noeud.droite = self._rotation_droite(noeud.droite)
            return self._rotation_gauche(noeud)

        return noeud

    # ── Insertion ────────────────────────────────────────────────

    def _inserer(self, noeud, cle: float, vetement: Vetement) -> NoeudAVL:
        if not noeud:
            return NoeudAVL(cle, vetement)
        if cle < noeud.cle:
            noeud.gauche = self._inserer(noeud.gauche, cle, vetement)
        else:
            noeud.droite = self._inserer(noeud.droite, cle, vetement)
        return self._equilibrer(noeud)

    def inserer(self, cle: float, vetement: Vetement):
        """
        Insère un vêtement trié par score.
        Complexité : O(log n).
        """
        self.racine = self._inserer(self.racine, cle, vetement)

    # ── Parcours en ordre décroissant ────────────────────────────

    def _parcours_decroissant(self, noeud, resultats: list):
        """Parcours droite → racine → gauche = ordre décroissant."""
        if not noeud:
            return
        self._parcours_decroissant(noeud.droite, resultats)
        resultats.append((noeud.cle, noeud.vetement))
        self._parcours_decroissant(noeud.gauche, resultats)

    def trier_decroissant(self) -> list:
        """
        Retourne les vêtements triés par score décroissant.
        Complexité : O(n) parcours infixe.
        """
        resultats = []
        self._parcours_decroissant(self.racine, resultats)
        return resultats


def trier_vetements_avl(utilisateur, scoring_fn=None) -> list:
    """
    Trie les vêtements par un score via AVL.

    Baseline  : sorted() recalculé à chaque appel → O(n log n)
    Optimisé  : AVL maintenu dynamiquement → O(log n) par insertion

    Args:
        utilisateur : instance Utilisateur
        scoring_fn  : fonction(Vetement) → float
                      par défaut : score basé sur propreté + complétude

    Returns:
        Liste de tuples (score, Vetement) triés par score décroissant
    """
    def score_defaut(v: Vetement) -> float:
        score = 0.0
        if v.est_propre:        score += 40
        if v.couleur_hex:       score += 20
        if v.style:             score += 20
        if v.saison != 'TOUTES_SAISONS': score += 20
        return score

    fn = scoring_fn or score_defaut
    avl = AVL()

    vetements = Vetement.objects.filter(utilisateur=utilisateur)
    for v in vetements:
        avl.inserer(fn(v), v)

    return avl.trier_decroissant()


# ─────────────────────────────────────────
#  STRUCTURE 3 : TABLE DE HACHAGE
#  Suggestion de remplacement O(1)
# ─────────────────────────────────────────

def construire_index_categorie_style(utilisateur) -> dict:
    """
    Construit une table de hachage : (categorie, style) → [Vetement]
    Pour suggestion de remplacement en O(1).

    Baseline  : scan linéaire O(n) pour trouver un remplacement
    Optimisé  : accès direct O(1) par clé (categorie, style)

    Complexité construction : O(n)
    Complexité accès        : O(1) amorti
    """
    index = {}
    vetements = Vetement.objects.filter(utilisateur=utilisateur, est_propre=True)
    for v in vetements:
        cle = (v.categorie, v.style or 'AUCUN')
        if cle not in index:
            index[cle] = []
        index[cle].append(v)
    return index


def suggerer_remplacement(vetement_sale: Vetement,
                           utilisateur) -> Vetement | None:
    """
    Suggère un vêtement propre similaire en remplacement.

    Logique :
      1. Cherche même catégorie + même style  → O(1)
      2. Si rien → même catégorie, style différent → O(1)
      3. Si rien → premier propre de la catégorie  → O(1)

    Baseline  : filtrer_vetements() → O(n) scan
    Optimisé  : index haché         → O(1) accès direct
    """
    index = construire_index_categorie_style(utilisateur)

    # 1. Même catégorie + même style
    cle_exacte = (vetement_sale.categorie, vetement_sale.style or 'AUCUN')
    candidats = index.get(cle_exacte, [])
    candidats = [v for v in candidats if v.id != vetement_sale.id]
    if candidats:
        return candidats[0]

    # 2. Même catégorie, n'importe quel style
    for cle, vetements in index.items():
        if cle[0] == vetement_sale.categorie:
            candidats = [v for v in vetements if v.id != vetement_sale.id]
            if candidats:
                return candidats[0]

    return None  # aucun remplacement disponible


# ─────────────────────────────────────────
#  COMPARAISON BASELINE VS OPTIMISÉ
# ─────────────────────────────────────────

def comparer_recherche(utilisateur, terme: str) -> dict:
    """
    Compare la recherche baseline vs Trie sur le même terme.
    Génère les métriques pour ton dossier algorithmique.
    """
    import time
    from wardrobe.services.base import rechercher_vetements

    # Baseline
    t0 = time.perf_counter()
    res_base = rechercher_vetements(utilisateur, terme)
    temps_base = time.perf_counter() - t0

    # Optimisé Trie
    t0 = time.perf_counter()
    res_opti = rechercher_vetements_trie(utilisateur, terme)
    temps_opti = time.perf_counter() - t0

    return {
        'terme':          terme,
        'baseline': {
            'resultats':  len(res_base),
            'temps_ms':   round(temps_base * 1000, 4),
            'methode':    'icontains O(n)',
        },
        'optimise': {
            'resultats':  len(res_opti),
            'temps_ms':   round(temps_opti * 1000, 4),
            'methode':    'Trie O(m)',
        },
        'gain_ms': round((temps_base - temps_opti) * 1000, 4),
    }
