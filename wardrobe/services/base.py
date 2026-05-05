from wardrobe.models import Vetement


# ─────────────────────────────────────────
#  CRUD DE BASE
# ─────────────────────────────────────────

def get_vetements_utilisateur(utilisateur) -> list:
    """
    Retourne tous les vêtements d'un utilisateur.
    Complexité : O(n) — parcours linéaire de la table.
    """
    return list(Vetement.objects.filter(utilisateur=utilisateur))


def get_vetement_par_id(vetement_id: int, utilisateur) -> Vetement | None:
    """
    Retourne un vêtement par son id.
    Complexité : O(1) — accès par clé primaire indexée.
    """
    try:
        return Vetement.objects.get(id=vetement_id, utilisateur=utilisateur)
    except Vetement.DoesNotExist:
        return None


def creer_vetement(utilisateur, nom: str, categorie: str,
                   couleur_hex: str = None, saison: str = 'TOUTES_SAISONS',
                   style: str = None, image_calque_url: str = None) -> Vetement:
    """
    Crée et sauvegarde un nouveau vêtement.
    """
    return Vetement.objects.create(
        utilisateur=utilisateur,
        nom=nom,
        categorie=categorie,
        couleur_hex=couleur_hex,
        saison=saison,
        style=style,
        image_calque_url=image_calque_url,
        est_propre=True
    )


def modifier_vetement(vetement_id: int, utilisateur, **kwargs) -> Vetement | None:
    """
    Modifie les champs d'un vêtement existant.
    Seuls les champs passés en kwargs sont modifiés.
    """
    vetement = get_vetement_par_id(vetement_id, utilisateur)
    if not vetement:
        return None
    champs_modifiables = {
        'nom', 'categorie', 'couleur_hex',
        'saison', 'style', 'image_calque_url', 'est_propre'
    }
    for champ, valeur in kwargs.items():
        if champ in champs_modifiables:
            setattr(vetement, champ, valeur)
    vetement.save()
    return vetement


def supprimer_vetement(vetement_id: int, utilisateur) -> bool:
    """
    Supprime un vêtement. Retourne True si supprimé, False si introuvable.
    """
    vetement = get_vetement_par_id(vetement_id, utilisateur)
    if not vetement:
        return False
    vetement.delete()
    return True


# ─────────────────────────────────────────
#  FILTRES ET RECHERCHE
# ─────────────────────────────────────────

def filtrer_vetements(utilisateur, categorie: str = None,
                      saison: str = None, style: str = None,
                      est_propre: bool = None) -> list:
    """
    Filtre les vêtements selon plusieurs critères combinés.
    Complexité : O(n) au pire, réduit par les index PostgreSQL.
    """
    qs = Vetement.objects.filter(utilisateur=utilisateur)

    if categorie:
        qs = qs.filter(categorie=categorie)
    if saison:
        qs = qs.filter(saison__in=[saison, 'TOUTES_SAISONS'])
    if style:
        qs = qs.filter(style=style)
    if est_propre is not None:
        qs = qs.filter(est_propre=est_propre)

    return list(qs)


def rechercher_vetements(utilisateur, terme: str) -> list:
    """
    Recherche des vêtements par nom (insensible à la casse).
    Utilise __icontains — équivalent LIKE %terme% en SQL.
    Complexité : O(n) — scan séquentiel sans index full-text.
    """
    if not terme or len(terme.strip()) == 0:
        return []
    return list(
        Vetement.objects.filter(
            utilisateur=utilisateur,
            nom__icontains=terme.strip()
        )
    )


# ─────────────────────────────────────────
#  LOGIQUE MÉTIER
# ─────────────────────────────────────────

def marquer_sale(vetement_id: int, utilisateur) -> Vetement | None:
    """
    Marque un vêtement comme sale (est_propre = False).
    Appelé après qu'une tenue a été portée.
    """
    return modifier_vetement(vetement_id, utilisateur, est_propre=False)


def marquer_propre(vetement_id: int, utilisateur) -> Vetement | None:
    """
    Marque un vêtement comme propre (est_propre = True).
    Appelé après lavage.
    """
    return modifier_vetement(vetement_id, utilisateur, est_propre=True)


def stats_garde_robe(utilisateur) -> dict:
    """
    Retourne des statistiques sur la garde-robe de l'utilisateur.
    Utile pour le dashboard et les logs de démo.

    Complexité : O(n) — un seul parcours via agrégations Django.
    """
    from django.db.models import Count

    total = Vetement.objects.filter(utilisateur=utilisateur)

    par_categorie = dict(
        total.values('categorie')
             .annotate(nb=Count('id'))
             .values_list('categorie', 'nb')
    )
    par_saison = dict(
        total.values('saison')
             .annotate(nb=Count('id'))
             .values_list('saison', 'nb')
    )

    nb_total   = total.count()
    nb_propres = total.filter(est_propre=True).count()
    nb_sales   = nb_total - nb_propres

    return {
        'total':         nb_total,
        'propres':       nb_propres,
        'sales':         nb_sales,
        'par_categorie': par_categorie,
        'par_saison':    par_saison,
        'garde_robe_ok': nb_total >= 3,  # minimum pour générer une tenue
    }


def vetements_disponibles_pour_tenue(utilisateur,
                                      saison: str = None,
                                      style: str = None) -> dict:
    """
    Retourne les vêtements propres disponibles groupés par catégorie.
    Appelé par outfits/services avant la génération de tenue.

    Returns:
        {
            'hauts': [...],
            'bas': [...],
            'accessoires': [...],
            'suffisant': bool  — True si au moins 1 haut ET 1 bas
        }
    """
    hauts = filtrer_vetements(
        utilisateur, categorie='HAUT', saison=saison,
        style=style, est_propre=True
    )
    bas = filtrer_vetements(
        utilisateur, categorie='BAS', saison=saison,
        style=style, est_propre=True
    )
    accessoires = filtrer_vetements(
        utilisateur, categorie='ACCESSOIRE', est_propre=True
    )

    return {
        'hauts':       hauts,
        'bas':         bas,
        'accessoires': accessoires,
        'suffisant':   len(hauts) >= 1 and len(bas) >= 1,
    }