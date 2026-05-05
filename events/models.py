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
    nom_evt        = models.CharField(max_length=100, null=True, blank=True,
                                      db_column='nom_evt')
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
    contenu     = models.TextField()
    date_envoi  = models.DateTimeField(auto_now_add=True)
    est_lue     = models.BooleanField(default=False)
    evenement   = models.ForeignKey(
                      Evenement,
                      null=True,
                      blank=True,
                      on_delete=models.CASCADE,
                      related_name='notifications',
                      db_column='id_evt'
                  )
    utilisateur = models.ForeignKey(
                      Utilisateur,
                      on_delete=models.CASCADE,
                      related_name='notifications',
                      db_column='id_user'
                  )

    def __str__(self):
        return f"Notification {self.id}"

    class Meta:
        db_table     = 'notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'