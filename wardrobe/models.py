from django.db import models
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

    nom              = models.CharField(max_length=100)
    categorie        = models.CharField(max_length=20, choices=Categorie.choices)
    couleur_hex      = models.CharField(max_length=7, null=True, blank=True)
    est_propre       = models.BooleanField(default=True)
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