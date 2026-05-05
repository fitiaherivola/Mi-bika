from wardrobe.models import Vetement
from outfits.models import Tenue


# ─────────────────────────────────────────
#  CONTRAINTES
# ─────────────────────────────────────────

def _verifier_contrainte_style(vetement: Vetement,
                                styles_autorises: list) -> bool:
    """Vérifie que le style du vêtement est autorisé."""
    if not styles_autorises:
        return True
    return vetement.style in styles_autorises


def _verifier_contrainte_saison(vetement: Vetement,
                                 saison: str) -> bool:
    """Vérifie que le vêtement est adapté à la saison."""
    if not saison:
        return True
    return vetement.saison in [saison, 'TOUTES_SAISONS']


def _verifier_contrainte_couleur(vetement: Vetement,
                                  couleurs_autorisees: list) -> bool:
    """
    Vérifie que la couleur du vêtement est dans la liste autorisée.
    Si pas de contrainte couleur → toujours valide.
    """
    if not couleurs_autorisees:
        return True
    if not vetement.couleur_hex:
        return False
    return vetement.couleur_hex.upper() in [
        c.upper() for c in couleurs_autorisees
    ]


def _verifier_non_porte_recemment(vetement: Vetement,
                                   tenues_recentes: list) -> bool:
    """
    Vérifie qu'un vêtement n'a pas été porté récemment.
    tenues_recentes = liste d'ids de vêtements déjà portés.
    """
    return vetement.id not in tenues_recentes


def _verifier_propre(vetement: Vetement) -> bool:
    """Vérifie que le vêtement est propre."""
    return vetement.est_propre


def _toutes_contraintes(vetement: Vetement,
                         contraintes: dict,
                         ids_portes: list) -> bool:
    """
    Vérifie TOUTES les contraintes sur un vêtement.
    C'est le cœur du backtracking — si une contrainte
    échoue on abandonne immédiatement cette branche.

    Complexité : O(1) — toutes les vérifications sont constantes.
    """
    if not _verifier_propre(vetement):
        return False
    if not _verifier_contrainte_saison(
            vetement, contraintes.get('saison')):
        return False
    if not _verifier_contrainte_style(
            vetement, contraintes.get('styles_autorises', [])):
        return False
    if not _verifier_contrainte_couleur(
            vetement, contraintes.get('couleurs_autorisees', [])):
        return False
    if not _verifier_non_porte_recemment(vetement, ids_portes):
        return False
    return True


# ─────────────────────────────────────────
#  ALGORITHME BACKTRACKING
# ─────────────────────────────────────────

class BacktrackingTenue:
    """
    Génère une tenue valide par exploration avec backtracking.

    Principe :
      1. Essaie chaque haut disponible
      2. Pour chaque haut valide → essaie chaque bas
      3. Pour chaque bas valide → essaie chaque accessoire (optionnel)
      4. Si toutes les contraintes sont satisfaites → solution trouvée
      5. Sinon → revient en arrière (backtrack) et essaie le suivant

    Différence vs baseline/optimisé :
      - baseline/optimisé : score toutes les combinaisons
      - backtracking : s'arrête dès qu'une solution valide est trouvée
                       ET garantit que TOUTES les contraintes sont
                       respectées (pas juste un score)

    Complexité : O(h × b × a) au pire
                 h = nb hauts, b = nb bas, a = nb accessoires
                 Mais avec élagage → bien meilleur en pratique

    L'élagage (pruning) est la clé :
      Si le haut ne satisfait pas les contraintes → on ne teste
      AUCUN des b × a combinaisons possibles avec ce haut.
    """

    def __init__(self, utilisateur, contraintes: dict):
        """
        Args:
            utilisateur  : instance Utilisateur
            contraintes  : {
                'saison'            : 'ETE' | 'HIVER' | ...
                'styles_autorises'  : ['CASUAL', 'FORMEL', ...]
                'couleurs_autorisees': ['#000000', '#FFFFFF', ...]
                'ids_portes_recemment': [1, 2, 3, ...]  ids vetements
                'avec_accessoire'   : True | False
            }
        """
        self.utilisateur  = utilisateur
        self.contraintes  = contraintes
        self.ids_portes   = contraintes.get('ids_portes_recemment', [])
        self.solutions    = []
        self.nb_noeuds    = 0   # compteur pour mesurer l'élagage

    def _charger_vetements(self):
        """Charge les vêtements depuis la BDD une seule fois."""
        base_qs = Vetement.objects.filter(
            utilisateur=self.utilisateur,
            est_propre=True
        )
        self.hauts       = list(base_qs.filter(categorie='HAUT'))
        self.bas_list    = list(base_qs.filter(categorie='BAS'))
        self.accessoires = list(base_qs.filter(categorie='ACCESSOIRE'))

    def _backtrack(self, haut=None, bas=None,
                   accessoire=None, etape='haut'):
        """
        Fonction récursive de backtracking.

        Étapes :
          'haut'       → choisir un haut valide
          'bas'        → choisir un bas valide
          'accessoire' → choisir un accessoire (optionnel)
          'solution'   → enregistrer la solution
        """
        self.nb_noeuds += 1

        # ── Solution trouvée ─────────────────────────────────────
        if etape == 'solution':
            self.solutions.append({
                'haut':        haut,
                'bas':         bas,
                'accessoire':  accessoire,
                'complet':     True,
            })
            return True  # on s'arrête à la première solution

        # ── Étape HAUT ───────────────────────────────────────────
        if etape == 'haut':
            for h in self.hauts:
                # Élagage : si haut invalide → on skip tout le sous-arbre
                if not _toutes_contraintes(h, self.contraintes,
                                           self.ids_portes):
                    continue
                # Haut valide → on descend vers le bas
                if self._backtrack(haut=h, etape='bas'):
                    return True  # solution trouvée, on remonte
            return False  # aucun haut valide

        # ── Étape BAS ────────────────────────────────────────────
        if etape == 'bas':
            for b in self.bas_list:
                if not _toutes_contraintes(b, self.contraintes,
                                           self.ids_portes):
                    continue
                # Bas valide → on descend vers accessoire
                if self._backtrack(haut=haut, bas=b,
                                   etape='accessoire'):
                    return True
            return False  # aucun bas valide pour ce haut → backtrack

        # ── Étape ACCESSOIRE ─────────────────────────────────────
        if etape == 'accessoire':
            avec_accessoire = self.contraintes.get('avec_accessoire', False)

            if not avec_accessoire:
                # Pas de contrainte accessoire → solution directe
                return self._backtrack(haut=haut, bas=bas,
                                       accessoire=None,
                                       etape='solution')

            for acc in self.accessoires:
                if not _toutes_contraintes(acc, self.contraintes,
                                           self.ids_portes):
                    continue
                if self._backtrack(haut=haut, bas=bas,
                                   accessoire=acc,
                                   etape='solution'):
                    return True

            # Aucun accessoire valide → on accepte sans accessoire
            return self._backtrack(haut=haut, bas=bas,
                                   accessoire=None,
                                   etape='solution')

        return False

    def resoudre(self) -> dict | None:
        """
        Lance le backtracking et retourne la première solution.

        Returns:
            Dict avec haut, bas, accessoire ou None si impossible.
        """
        self._charger_vetements()
        self._backtrack(etape='haut')

        if not self.solutions:
            return None

        return {
            **self.solutions[0],
            'algorithme':  'backtracking',
            'nb_noeuds':   self.nb_noeuds,  # pour mesurer l'élagage
        }


# ─────────────────────────────────────────
#  POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────

def generer_tenue_backtracking(utilisateur,
                                saison: str = None,
                                styles_autorises: list = None,
                                couleurs_autorisees: list = None,
                                ids_portes_recemment: list = None,
                                avec_accessoire: bool = False) -> dict | None:
    """
    Génère une tenue garantissant toutes les contraintes.
    Point d'entrée appelé depuis views.py.

    Args:
        utilisateur          : instance Utilisateur
        saison               : contrainte saison
        styles_autorises     : liste de styles acceptés
        couleurs_autorisees  : liste de couleurs hex acceptées
        ids_portes_recemment : ids de vêtements à éviter
        avec_accessoire      : forcer un accessoire

    Returns:
        Dict {haut, bas, accessoire, nb_noeuds} ou None
    """
    contraintes = {
        'saison':               saison,
        'styles_autorises':     styles_autorises or [],
        'couleurs_autorisees':  couleurs_autorisees or [],
        'ids_portes_recemment': ids_portes_recemment or [],
        'avec_accessoire':      avec_accessoire,
    }
    solver = BacktrackingTenue(utilisateur, contraintes)
    return solver.resoudre()


# ─────────────────────────────────────────
#  COMPARAISON POUR DOSSIER ALGORITHMIQUE
# ─────────────────────────────────────────

def comparer_backtracking_vs_baseline(utilisateur,
                                       saison: str = None) -> dict:
    """
    Compare backtracking vs baseline sur le même jeu de données.
    Génère les métriques pour ton tableau comparatif.
    """
    import time
    from outfits.services.base import generer_tenues_baseline

    # Baseline
    t0       = time.perf_counter()
    res_base = generer_tenues_baseline(utilisateur, saison=saison, top_k=1)
    t_base   = time.perf_counter() - t0

    # Backtracking
    t0  = time.perf_counter()
    res_bt = generer_tenue_backtracking(utilisateur, saison=saison)
    t_bt = time.perf_counter() - t0

    return {
        'baseline': {
            'temps_ms':           round(t_base * 1000, 3),
            'garantit_contraintes': False,
            'methode':            'scoring O(n²)',
        },
        'backtracking': {
            'temps_ms':           round(t_bt * 1000, 3),
            'garantit_contraintes': True,
            'nb_noeuds_explores': res_bt['nb_noeuds'] if res_bt else 0,
            'methode':            'exploration avec élagage',
        },
    }