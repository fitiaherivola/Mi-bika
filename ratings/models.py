from django.db import models
from users.models import Utilisateur


class Humeur(models.Model):
    """Modèle pour les humeurs/sentiments de l'utilisateur."""
    HUMEUR_CHOICES = [
        ('heureuse', 'Heureuse'),
        ('triste', 'Triste'),
        ('neutre', 'Neutre'),
        ('enervee', 'Énervée'),
        ('calme', 'Calme'),
        ('excitee', 'Excitée'),
    ]

    type_humeur = models.CharField(max_length=20, choices=HUMEUR_CHOICES)
    date_saisie = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='humeurs')

    def __str__(self):
        return f"{self.utilisateur.pseudo} - {self.get_type_humeur_display()}"

    class Meta:
        verbose_name = "Humeur"
        verbose_name_plural = "Humeurs"
