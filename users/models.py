from django.db import models


class Utilisateur(models.Model):

    class StylePrefere(models.TextChoices):
        CASUAL       = 'CASUAL',       'Casual'
        FORMEL       = 'FORMEL',       'Formel'
        SPORT        = 'SPORT',        'Sport'
        TRADITIONNEL = 'TRADITIONNEL', 'Traditionnel'
        SOIREE       = 'SOIREE',       'Soirée'
        BOHEME       = 'BOHEME',       'Bohème'

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

    pseudo        = models.CharField(max_length=50, unique=True)
    style_prefere = models.CharField(
                        max_length=20,
                        choices=StylePrefere.choices,
                        null=True,
                        blank=True
                    )
    teint_avatar  = models.CharField(
                        max_length=7,
                        null=True,
                        blank=True
                    )
    morphologie   = models.CharField(
                        max_length=20,
                        choices=Morphologie.choices,
                        null=True,
                        blank=True
                    )

    class Meta:
        db_table            = 'utilisateur'
        verbose_name        = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return self.pseudo