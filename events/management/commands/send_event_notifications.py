from django.core.management.base import BaseCommand

from events.services.notifications import (
    verifier_rappels_evenements,
    verifier_alertes_meteo,
)


class Command(BaseCommand):
    help = 'Envoie les notifications intelligentes (rappels événements, alertes météo).'

    def add_arguments(self, parser):
        parser.add_argument('--ville', default='Antananarivo')

    def handle(self, *args, **options):
        n_evt = verifier_rappels_evenements()
        n_meteo = verifier_alertes_meteo(options['ville'])
        self.stdout.write(
            self.style.SUCCESS(
                f'Notifications créées : {n_evt} événement(s), {n_meteo} météo.'
            )
        )
