"""
Déduit le style vestimentaire adapté à un événement (type explicite ou nom).
"""
from typing import Optional

from wardrobe.models import Vetement

# Type d'événement → style de tenue cible
TYPE_EVT_TO_STYLE = {
    'MARIAGE':       'TRADITIONNEL',
    'TRADITIONNEL':  'TRADITIONNEL',
    'SOIREE':        'SOIREE',
    'PROFESSIONNEL': 'FORMEL',
    'SPORT':         'SPORT',
    'CASUAL':        'CASUAL',
    'AUTRE':         None,
}

# Mots-clés dans le nom (si type = AUTRE ou absent)
MOTS_CLES_STYLE = [
    (('mariage', 'noces', 'fiancailles'), 'TRADITIONNEL'),
    (('soiree', 'soirée', 'gala', 'cocktail', 'anniversaire'), 'SOIREE'),
    (('sport', 'course', 'match', 'entrainement', 'entraînement'), 'SPORT'),
    (('travail', 'bureau', 'reunion', 'réunion', 'entretien', 'professionnel'), 'FORMEL'),
    (('lamba', 'tradition', 'traditionnel', 'ceremonie', 'cérémonie', 'famadihana'), 'TRADITIONNEL'),
    (('decontracte', 'décontracté', 'barbecue', 'pique-nique', 'picnic'), 'CASUAL'),
    (('boheme', 'bohème', 'nature', 'hippie', 'plage', 'outdoor'), 'BOHEME'),
    (('retro', 'rétro', 'vintage', 'ancien', 'kermesse'), 'RETRO'),
    (('grunge', 'rock', 'metal', 'concert', 'underground'), 'GRUNGE'),
    (('chic', 'classe', 'elegant', 'élégant', 'dinner', 'dîner', 'opera', 'opéra'), 'CHIC'),
    (('streetwear', 'street', 'skate', 'urbain', 'urban'), 'STREETWEAR'),
]


def inferer_style_depuis_nom(nom_evt: str) -> Optional[str]:
    if not nom_evt:
        return None
    nom = nom_evt.lower()
    for mots, style in MOTS_CLES_STYLE:
        if any(m in nom for m in mots):
            return style
    return None


def determiner_style_evenement(evenement) -> Optional[str]:
    """
    Style vestimentaire pour générer une tenue liée à cet événement.
    Priorité : type_evt explicite → mots-clés du nom → style préféré utilisateur.
    """
    type_evt = getattr(evenement, 'type_evt', None) or 'AUTRE'
    if type_evt != 'AUTRE':
        style = TYPE_EVT_TO_STYLE.get(type_evt)
        if style:
            return style

    style_nom = inferer_style_depuis_nom(evenement.nom_evt or '')
    if style_nom:
        return style_nom

    return getattr(evenement.utilisateur, 'style_prefere', None)


def garde_robe_contient_style(utilisateur, style: str) -> bool:
    if not style:
        return False
    return Vetement.objects.filter(
        utilisateur=utilisateur,
        est_propre=True,
        style=style,
        categorie__in=('HAUT', 'BAS'),
    ).exists()
