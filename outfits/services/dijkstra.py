"""
Algorithme de Dijkstra pour trouver la tenue la plus harmonieuse.

Modélisation :
  - Chaque vêtement est un nœud dans un graphe bipartite orienté.
  - Niveau 1 : hauts    (catégorie HAUT)
  - Niveau 2 : bas      (catégorie BAS)
  - Niveau 3 : accessoires (catégorie ACCESSOIRE)

Arêtes :
  - Source → Haut   : poids 0
  - Haut → Bas      : poids = (50 - score_compatibilite(haut, bas)) / 100
  - Bas  → Accessoire: poids = (50 - score_compatibilite(bas, accessoire)) / 100
  - Bas/Accessoire → Puits : poids 0

Chemin optimal :
  - Dijkstra depuis la source virtuelle vers le puits virtuel
  - Chemin de coût minimal = harmonie de paires maximale le long des arêtes

Complexité : O((V + E) log V) avec tas min ; E = O(h×b + b×a)
"""

import heapq
from collections import defaultdict
from typing import Optional

from wardrobe.models import Vetement
from outfits.services.base import _score_compatibilite_couleur


# ─────────────────────────────────────────
#  POIDS D'ARÊTE
# ─────────────────────────────────────────

def _edge_weight(v1: Vetement, v2: Vetement) -> float:
    """
    Poids d'une arête entre deux vêtements consécutifs.
    0 = paire parfaite, 0.5 = paire incompatible (score couleur+style nul).
    """
    score_couleur = _score_compatibilite_couleur(v1.couleur_hex, v2.couleur_hex)
    style_bonus = 20 if (v1.style and v2.style and v1.style == v2.style) else 0
    score_pair = score_couleur + style_bonus  # max 50
    return (50 - score_pair) / 100.0


def _compute_harmony_score_full(
    haut: Vetement, bas: Vetement, accessoire: Optional[Vetement] = None
) -> int:
    """Score d'harmonie complet (0-100) via le baseline."""
    from outfits.services.base import calculer_score_baseline

    return calculer_score_baseline(haut, bas, accessoire)


# ─────────────────────────────────────────
#  CONSTRUCTION DU GRAPHE
# ─────────────────────────────────────────

def _build_outfit_graph(
    hauts: list,
    bas_list: list,
    accessoires: list,
    avec_accessoire: bool,
) -> tuple[dict, tuple, tuple, dict]:
    """
    Construit la liste d'adjacence du graphe à 3 couches + source/puits.

    Returns:
        (graph, source, sink, id_to_vetement)
    """
    graph: dict = defaultdict(list)
    id_to_vetement: dict[int, Vetement] = {}

    for v in hauts + bas_list + accessoires:
        id_to_vetement[v.id] = v

    source = ('src',)
    sink = ('sink',)

    for h in hauts:
        graph[source].append((('h', h.id), 0.0))

    for h in hauts:
        h_node = ('h', h.id)
        for b in bas_list:
            graph[h_node].append((('b', b.id), _edge_weight(h, b)))

    need_accessory = avec_accessoire and bool(accessoires)

    for b in bas_list:
        b_node = ('b', b.id)
        if need_accessory:
            for a in accessoires:
                graph[b_node].append((('a', a.id), _edge_weight(b, a)))
        else:
            graph[b_node].append((sink, 0.0))

    if need_accessory:
        for a in accessoires:
            graph[('a', a.id)].append((sink, 0.0))

    return graph, source, sink, id_to_vetement


# ─────────────────────────────────────────
#  DIJKSTRA
# ─────────────────────────────────────────

def _dijkstra_shortest_path(
    graph: dict,
    source: tuple,
    sink: tuple,
) -> tuple[Optional[float], list]:
    """
    Dijkstra classique : tas min, distances, prédécesseurs.

    Returns:
        (coût_minimal, chemin_nœuds) ou (None, []) si inaccessible.
    """
    dist: dict[tuple, float] = {source: 0.0}
    prev: dict[tuple, Optional[tuple]] = {source: None}
    heap: list = [(0.0, 0, source)]
    counter = 1

    while heap:
        d, _, u = heapq.heappop(heap)
        if d > dist.get(u, float('inf')):
            continue
        if u == sink:
            break

        for v, weight in graph.get(u, []):
            nd = d + weight
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, counter, v))
                counter += 1

    if sink not in dist:
        return None, []

    path: list = []
    node = sink
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return dist[sink], path


def _path_to_outfit(
    path: list, id_to_vetement: dict[int, Vetement]
) -> tuple[Optional[Vetement], Optional[Vetement], Optional[Vetement]]:
    """Extrait (haut, bas, accessoire) depuis la liste de nœuds du chemin."""
    haut = bas = accessoire = None
    for node in path:
        kind = node[0]
        if kind == 'h':
            haut = id_to_vetement[node[1]]
        elif kind == 'b':
            bas = id_to_vetement[node[1]]
        elif kind == 'a':
            accessoire = id_to_vetement[node[1]]
    return haut, bas, accessoire


# ─────────────────────────────────────────
#  POINT D'ENTRÉE DIJKSTRA
# ─────────────────────────────────────────

def dijkstra_most_harmonious_outfit(
    utilisateur,
    saison: str = None,
    style: str = None,
    avec_accessoire: bool = True,
) -> Optional[dict]:
    """
    Trouve la tenue la plus harmonieuse en utilisant Dijkstra.

    1. Filtre les vêtements (saison, style)
    2. Construit le graphe orienté Source → Haut → Bas → [Accessoire] → Puits
    3. Exécute Dijkstra (tas min) pour le chemin de coût minimal
    4. Reconstruit la tenue et calcule le score baseline complet

    Returns:
        Dict {haut, bas, accessoire, score_harmonie, algorithme, cost}
        ou None si pas de solution.
    """
    all_hauts = Vetement.objects.filter(
        utilisateur=utilisateur, categorie='HAUT', est_propre=True
    )
    all_bas = Vetement.objects.filter(
        utilisateur=utilisateur, categorie='BAS', est_propre=True
    )
    all_accessoires = Vetement.objects.filter(
        utilisateur=utilisateur, categorie='ACCESSOIRE', est_propre=True
    )

    if saison:
        all_hauts = all_hauts.filter(saison__in=[saison, 'TOUTES_SAISONS'])
        all_bas = all_bas.filter(saison__in=[saison, 'TOUTES_SAISONS'])
        all_accessoires = all_accessoires.filter(saison__in=[saison, 'TOUTES_SAISONS'])
    if style:
        all_hauts = all_hauts.filter(style=style)
        all_bas = all_bas.filter(style=style)
        all_accessoires = all_accessoires.filter(style=style)

    hauts = list(all_hauts)
    bas_list = list(all_bas)
    accessoires = list(all_accessoires)

    if not hauts or not bas_list:
        return None

    graph, source, sink, id_to_vetement = _build_outfit_graph(
        hauts, bas_list, accessoires, avec_accessoire
    )

    meilleur_cost, path = _dijkstra_shortest_path(graph, source, sink)
    if meilleur_cost is None or not path:
        return None

    haut, bas, accessoire = _path_to_outfit(path, id_to_vetement)
    if haut is None or bas is None:
        return None

    score_final = _compute_harmony_score_full(haut, bas, accessoire)

    return {
        'haut': haut,
        'bas': bas,
        'accessoire': accessoire,
        'score_harmonie': score_final,
        'algorithme': 'dijkstra',
        'cost': round(meilleur_cost, 4),
    }


def generer_tenue_dijkstra(
    utilisateur,
    saison: str = None,
    style: str = None,
    avec_accessoire: bool = True,
) -> Optional[dict]:
    """Point d'entrée pour générer une tenue optimale via Dijkstra."""
    return dijkstra_most_harmonious_outfit(
        utilisateur=utilisateur,
        saison=saison,
        style=style,
        avec_accessoire=avec_accessoire,
    )


def comparer_dijkstra_vs_baseline(utilisateur, saison: str = None) -> dict:
    """
    Compare Dijkstra vs baseline sur une tenue.
    Retourne les métriques pour dossier algorithmique.
    """
    import time
    from outfits.services.base import generer_tenues_baseline

    t0 = time.perf_counter()
    res_base = generer_tenues_baseline(utilisateur, saison=saison, top_k=1)
    t_base = time.perf_counter() - t0

    t0 = time.perf_counter()
    res_dj = generer_tenue_dijkstra(utilisateur, saison=saison)
    t_dj = time.perf_counter() - t0

    score_base = res_base[0]['score_harmonie'] if res_base else 0
    score_dj = res_dj['score_harmonie'] if res_dj else 0

    return {
        'baseline': {
            'temps_ms': round(t_base * 1000, 3),
            'score': score_base,
            'methode': 'O(n²) heap top-k',
        },
        'dijkstra': {
            'temps_ms': round(t_dj * 1000, 3),
            'score': score_dj,
            'methode': 'graphe + Dijkstra O((V+E) log V)',
        },
        'gain_score': round(score_dj - score_base, 2),
    }
