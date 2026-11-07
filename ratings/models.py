from django.db import models
from users.models import Utilisateur
from outfits.models import Tenue


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
        return f"{self.utilisateur.username} - {self.get_type_humeur_display()}"

    class Meta:
        db_table = 'humeur'
        verbose_name = "Humeur"
        verbose_name_plural = "Humeurs"


class Notation(models.Model):
    """
    Modèle pour l'historique des notations de tenues.
    Permet à l'utilisateur de noter les tenues proposées
    et alimente le système d'apprentissage des préférences.
    """

    NOTE_CHOICES = [
        (1, '⭐ Très mauvaise'),
        (2, '⭐⭐ Mauvaise'),
        (3, '⭐⭐⭐ Correct'),
        (4, '⭐⭐⭐⭐ Bonne'),
        (5, '⭐⭐⭐⭐⭐ Excellente'),
    ]

    note          = models.IntegerField(choices=NOTE_CHOICES, help_text="Note de 1 à 5 étoiles")
    commentaire   = models.TextField(null=True, blank=True, help_text="Commentaire optionnel de l'utilisateur")
    date_notation = models.DateTimeField(auto_now_add=True)
    est_portee    = models.BooleanField(
        default=False,
        help_text="La tenue a-t-elle finalement été portée ce jour ?"
    )
    tenue         = models.ForeignKey(
        Tenue,
        on_delete=models.CASCADE,
        related_name='notations',
        db_column='id_tenue'
    )
    utilisateur   = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notations',
        db_column='id_user'
    )

    class Meta:
        db_table = 'notation'
        verbose_name = 'Notation'
        verbose_name_plural = 'Notations'
        ordering = ['-date_notation']

    def __str__(self):
        return f"{self.utilisateur.username} - Tenue #{self.tenue.id} : {self.get_note_display()}"
