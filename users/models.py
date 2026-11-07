from django.db import models
from django.contrib.auth.models import AbstractUser


class Utilisateur(AbstractUser):

    # ─────────────────────────────────────────
    #  ENUMS (TextChoices)
    # ─────────────────────────────────────────

    class StylePrefere(models.TextChoices):
        CASUAL       = 'CASUAL',       'Casual'
        FORMEL       = 'FORMEL',       'Formel'
        SPORT        = 'SPORT',        'Sport'
        TRADITIONNEL = 'TRADITIONNEL', 'Traditionnel'
        SOIREE       = 'SOIREE',       'Soirée'
        BOHEME       = 'BOHEME',       'Bohème'
        RETRO        = 'RETRO',        'Rétro / Vintage'
        GRUNGE       = 'GRUNGE',       'Grunge'
        CHIC         = 'CHIC',         'Chic'
        STREETWEAR   = 'STREETWEAR',   'Streetwear'

    class Morphologie(models.TextChoices):
        SABLIER      = 'SABLIER',      'Sablier'
        RECTANGLE    = 'RECTANGLE',    'Rectangle'
        TRIANGLE     = 'TRIANGLE',     'Triangle'
        TRIANGLE_INV = 'TRIANGLE_INV', 'Triangle inversé'
        RONDE        = 'RONDE',        'Ronde'

    class TeintAvatar(models.TextChoices):
        CLAIR      = 'CLAIR',      'Clair'
        MEDIUM     = 'MEDIUM',     'Médium'
        MATE       = 'MATE',       'Maté'
        FONCE      = 'FONCE',      'Foncé'
        TRES_FONCE = 'TRES_FONCE', 'Très foncé'

    # ─────────────────────────────────────────
    #  CHAMPS PERSO Mi-bika
    # ─────────────────────────────────────────
    # ⚠️ Pas de champ `pseudo` : AbstractUser fournit déjà `username` (unique)

    style_prefere = models.CharField(
        max_length=20,
        choices=StylePrefere.choices,
        null=True,
        blank=True,
    )

    teint_avatar = models.CharField(
        max_length=10,
        choices=TeintAvatar.choices,
        null=True,
        blank=True,
    )

    morphologie = models.CharField(
        max_length=20,
        choices=Morphologie.choices,
        null=True,
        blank=True,
    )

    photo_profil = models.TextField(
        null=True,
        blank=True,
    )

    # ─────────────────────────────────────────
    #  META
    # ─────────────────────────────────────────

    class Meta:
        db_table            = 'utilisateur'
        verbose_name        = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return self.username
