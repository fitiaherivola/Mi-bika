from django.db import models


class Tendance(models.Model):

    class Style(models.TextChoices):
        CASUAL       = 'CASUAL',       'Casual'
        FORMEL       = 'FORMEL',       'Formel'
        SPORT        = 'SPORT',        'Sport'
        TRADITIONNEL = 'TRADITIONNEL', 'Traditionnel'
        SOIREE       = 'SOIREE',       'Soirée'

    titre         = models.CharField(max_length=200)
    description   = models.TextField(null=True, blank=True)
    style         = models.CharField(max_length=20,
                                     choices=Style.choices,
                                     null=True, blank=True)
    popularite    = models.IntegerField(default=0)
    image_url     = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_fin      = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table     = 'tendance'
        verbose_name = 'Tendance'

    def __str__(self):
        return self.titre

class Boutique(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    style_dominant = models.CharField(
        max_length=20,
        choices=Tendance.Style.choices,
        null=True, blank=True
    )
    adresse = models.CharField(max_length=255, null=True, blank=True)
    instagram_url = models.URLField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    popularite = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'boutique'
        verbose_name = 'Boutique'

    def __str__(self):
        return self.nom