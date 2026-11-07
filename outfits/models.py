from django.db import models
from users.models import Utilisateur
from wardrobe.models import Vetement


class Tenue(models.Model):

    class ScoreHarmonie(models.IntegerChoices):
        MIN = 0,   'Minimum'
        MAX = 100, 'Maximum'

    date_creation   = models.DateTimeField(auto_now_add=True)
    score_harmonie  = models.IntegerField(
                          default=0,
                          help_text="Score de 0 à 100"
                      )
    algorithme      = models.CharField(
                          max_length=32,
                          blank=True,
                          default='',
                          help_text="Algorithme ayant généré la tenue (baseline, optimise, dijkstra, …)",
                      )
    haut            = models.ForeignKey(
                          Vetement,
                          null=True,
                          blank=True,
                          on_delete=models.SET_NULL,
                          related_name='tenues_haut',
                          db_column='id_haut'
                      )
    bas             = models.ForeignKey(
                          Vetement,
                          null=True,
                          blank=True,
                          on_delete=models.SET_NULL,
                          related_name='tenues_bas',
                          db_column='id_bas'
                      )
    accessoire      = models.ForeignKey(
                          Vetement,
                          null=True,
                          blank=True,
                          on_delete=models.SET_NULL,
                          related_name='tenues_accessoire',
                          db_column='id_accessoire'
                      )
    utilisateur     = models.ForeignKey(
                          Utilisateur,
                          on_delete=models.CASCADE,
                          related_name='tenues',
                          db_column='id_user'
                      )

    class Meta:
        db_table    = 'tenue'
        verbose_name = 'Tenue'
        verbose_name_plural = 'Tenues'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(score_harmonie__gte=0) & models.Q(score_harmonie__lte=100),
                name='tenue_score_harmonie_check'
)

        ]

    def __str__(self):
        return f"Tenue {self.id} — score {self.score_harmonie}/100"

    def est_complete(self):
        """Vérifie qu'une tenue a au moins un haut et un bas."""
        return self.haut is not None and self.bas is not None