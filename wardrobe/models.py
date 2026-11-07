from django.db import models
from django.utils import timezone
from users.models import Utilisateur


class Vetement(models.Model):

    class Categorie(models.TextChoices):
        HAUT        = 'HAUT',        'Haut'
        BAS         = 'BAS',         'Bas'
        ACCESSOIRE  = 'ACCESSOIRE',  'Accessoire'

    class Saison(models.TextChoices):
        ETE             = 'ETE',            'Été'
        HIVER           = 'HIVER',          'Hiver'
        PRINTEMPS       = 'PRINTEMPS',      'Printemps'
        AUTOMNE         = 'AUTOMNE',        'Automne'
        TOUTES_SAISONS  = 'TOUTES_SAISONS', 'Toutes saisons'

    class Style(models.TextChoices):
        CASUAL          = 'CASUAL',         'Casual'
        FORMEL          = 'FORMEL',         'Formel'
        SPORT           = 'SPORT',          'Sport'
        TRADITIONNEL    = 'TRADITIONNEL',   'Traditionnel'
        SOIREE          = 'SOIREE',         'Soirée'
        BOHEME          = 'BOHEME',         'Bohème'
        RETRO           = 'RETRO',          'Rétro / Vintage'
        GRUNGE          = 'GRUNGE',         'Grunge'
        CHIC            = 'CHIC',           'Chic'
        STREETWEAR      = 'STREETWEAR',     'Streetwear'

    nom              = models.CharField(max_length=100)
    categorie        = models.CharField(max_length=20, choices=Categorie.choices)
    couleur_hex      = models.CharField(max_length=7, null=True, blank=True)
    est_propre       = models.BooleanField(default=True)
    is_worn          = models.BooleanField(
        default=False,
        verbose_name='Déjà porté',
        help_text='Indique si le vêtement a déjà été porté au moins une fois.'
    )
    last_worn        = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Dernière fois porté',
        help_text='Date et heure du dernier port de ce vêtement.'
    )
    image_calque_url = models.TextField(null=True, blank=True)
    saison           = models.CharField(
                           max_length=20,
                           choices=Saison.choices,
                           default=Saison.TOUTES_SAISONS
                       )
    style            = models.CharField(
                           max_length=20,
                           choices=Style.choices,
                           null=True,
                           blank=True
                       )
    utilisateur      = models.ForeignKey(
                           Utilisateur,
                           on_delete=models.CASCADE,
                           related_name='vetements',
                           db_column='id_user'
                       )

    class Meta:
        db_table = 'vetement'
        verbose_name = 'Vêtement'
        verbose_name_plural = 'Vêtements'

    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"


class Contrainte(models.Model):
    """
    Modèle pour les contraintes personnelles quotidiennes.
    Permet à l'utilisateur de renseigner son état du jour
    (santé, lessive, temps disponible, anti-répétition).
    """

    class TypeContrainte(models.TextChoices):
        SANTE       = 'SANTE',       'Mode santé - vêtements confortables'
        LESSIVE     = 'LESSIVE',     'Lessive - minimiser vêtements sales'
        TEMPS       = 'TEMPS',       'Temps limité - tenues simples'
        REPETITION  = 'REPETITION',  'Éviter répétition - tenues déjà portées'

    type_contrainte = models.CharField(
        max_length=20,
        choices=TypeContrainte.choices
    )
    date_activation = models.DateField(auto_now_add=True)
    priorite        = models.IntegerField(
        default=1,
        help_text="1=basse, 2=moyenne, 3=haute. Plus élevé = prime sur autres facteurs"
    )
    utilisateur     = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='contraintes',
        db_column='id_user'
    )

    class Meta:
        db_table = 'contrainte'
        verbose_name = 'Contrainte personnelle'
        verbose_name_plural = 'Contraintes personnelles'

    def __str__(self):
        return f"{self.utilisateur.username} - {self.get_type_contrainte_display()}"