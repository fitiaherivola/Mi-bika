from django.db import models


class Meteo(models.Model):

    class Condition(models.TextChoices):
        ENSOLEILLE = 'ensoleille', 'Ensoleillé'
        PLUVIEUX   = 'pluvieux',   'Pluvieux'
        NUAGEUX    = 'nuageux',    'Nuageux'
        CHAUD      = 'chaud',      'Chaud'
        FROID      = 'froid',      'Froid'

    ville            = models.CharField(max_length=100)
    temperature      = models.FloatField()
    condition        = models.CharField(
                           max_length=20,
                           choices=Condition.choices,
                           default=Condition.NUAGEUX
                       )
    date_prediction  = models.DateField()
    derniere_maj     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'meteo_'
        verbose_name = 'Météo'
        verbose_name_plural = 'Météos'
        ordering     = ['-date_prediction']

    def __str__(self):
        return f"{self.ville} — {self.temperature}°C ({self.condition})"

    def saison_estimee(self) -> str:
        """
        Estime la saison depuis la température et la condition.
        Utilisé par outfits/services pour le scoring météo.
        """
        t = self.temperature
        if t >= 25:
            return 'ETE'
        elif t <= 10:
            return 'HIVER'
        elif self.condition in ['pluvieux', 'nuageux']:
            return 'AUTOMNE'
        else:
            return 'PRINTEMPS'
        

        