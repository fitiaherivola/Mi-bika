from django.core.management.base import BaseCommand
from feedback.models import FeedbackMessage


class Command(BaseCommand):
    help = 'Affiche le nombre de messages de feedback en attente'

    def handle(self, *args, **options):
        count = FeedbackMessage.objects.filter(
            statut=FeedbackMessage.Status.PENDING
        ).count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucun message de feedback en attente.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'{count} message(s) de feedback en attente de traitement.'
                )
            )