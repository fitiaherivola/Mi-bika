from django.db import models
from users.models import Utilisateur
from outfits.models import Tenue


class Calendrier(models.Model):
    nom_calendrier = models.CharField(max_length=100, null=True, blank=True)
    api_source_url = models.TextField(null=True, blank=True)
    utilisateur    = models.ForeignKey(
                         Utilisateur,
                         on_delete=models.CASCADE,
                         related_name='calendriers',
                         db_column='id_user'
                     )

    class Meta:
        db_table     = 'calendrier'
        verbose_name = 'Calendrier'

    def __str__(self):
        return self.nom_calendrier or f"Calendrier {self.id}"


class Evenement(models.Model):

    class TypeEvenement(models.TextChoices):
        MARIAGE       = 'MARIAGE',       'Mariage'
        SOIREE        = 'SOIREE',        'Soirée'
        PROFESSIONNEL = 'PROFESSIONNEL', 'Professionnel'
        SPORT         = 'SPORT',         'Sport'
        TRADITIONNEL  = 'TRADITIONNEL',  'Traditionnel / cérémonie'
        CASUAL        = 'CASUAL',        'Décontracté'
        AUTRE         = 'AUTRE',         'Autre'

    nom_evt        = models.CharField(max_length=100, null=True, blank=True,
                                      db_column='nom_evt')
    type_evt       = models.CharField(
                         max_length=20,
                         choices=TypeEvenement.choices,
                         default=TypeEvenement.AUTRE,
                         db_column='type_evt',
                     )
    date_evt       = models.DateTimeField(null=True, blank=True,
                                          db_column='date_evt')
    lieu           = models.CharField(max_length=100, null=True, blank=True)
    tenue_reservee = models.ForeignKey(
                         Tenue,
                         null=True,
                         blank=True,
                         on_delete=models.SET_NULL,
                         related_name='evenements',
                         db_column='id_tenue_reservee'
                     )
    calendrier     = models.ForeignKey(
                         Calendrier,
                         null=True,
                         blank=True,
                         on_delete=models.CASCADE,
                         related_name='evenements',
                         db_column='id_calendrier'
                     )
    utilisateur    = models.ForeignKey(
                         Utilisateur,
                         on_delete=models.CASCADE,
                         related_name='evenements',
                         db_column='id_user'
                     )

    def __str__(self):
        return self.nom_evt or f"Événement {self.id}"

    class Meta:
        db_table     = 'evenement'
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'


class Notification(models.Model):
    """
    Modèle pour les notifications intelligentes.
    Peut être liée à un événement (rappel avant événement)
    ou autonome (alerte météo, changement important).
    """

    class TypeNotification(models.TextChoices):
        EVENEMENT       = 'EVENEMENT',       'Rappel événement'
        METEO           = 'METEO',           'Alerte météo'
        TENUE_SUGGEREE  = 'TENUE_SUGGEREE',  'Suggestion de tenue'
        GENERAL         = 'GENERAL',         'Information générale'

    contenu         = models.TextField()
    type_notif      = models.CharField(
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.GENERAL
    )
    date_envoi      = models.DateTimeField(auto_now_add=True)
    est_lue         = models.BooleanField(default=False)
    evenement       = models.ForeignKey(
                          Evenement,
                          null=True,
                          blank=True,
                          on_delete=models.CASCADE,
                          related_name='notifications',
                          db_column='id_evt'
                      )
    utilisateur     = models.ForeignKey(
                          Utilisateur,
                          on_delete=models.CASCADE,
                          related_name='notifications',
                          db_column='id_user'
                      )

    class Meta:
        db_table = 'notification'
        verbose_name = 'Notification'
        ordering = ['-date_envoi']

    def __str__(self):
        return f"[{self.get_type_notif_display()}] {self.utilisateur.username} - {self.date_envoi.strftime('%d/%m %H:%M')}"