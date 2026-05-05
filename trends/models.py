from django.db import models


class Tendance(models.Model):
    """Modèle pour les tendances de mode."""
    titre = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    popularite = models.IntegerField(default=0)  # 0-100

    def __str__(self):
        return self.titre

    class Meta:
        verbose_name = "Tendance"
        verbose_name_plural = "Tendances"
