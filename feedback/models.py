from django.db import models
from users.models import Utilisateur


class FeedbackMessage(models.Model):
    """
    Modèle pour les messages de feedback des utilisateurs.
    Stocke les retours utilisateurs avec un statut de traitement.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        IN_PROGRESS = 'IN_PROGRESS', 'En cours de traitement'
        RESOLVED = 'RESOLVED', 'Résolu'

    sujet = models.CharField(max_length=200)
    message = models.TextField()
    statut = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        db_column='id_user'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback_message'
        verbose_name = 'Message de feedback'
        verbose_name_plural = 'Messages de feedback'
        ordering = ['-date_creation']

    def __str__(self):
        return f"[{self.get_statut_display()}] {self.sujet} — {self.utilisateur.username}"