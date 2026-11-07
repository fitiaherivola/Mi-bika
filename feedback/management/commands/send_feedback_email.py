import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from feedback.models import FeedbackMessage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envoie les emails de feedback non traités depuis les dernières 48h'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Affiche les emails sans les envoyer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        cutoff = now - timedelta(hours=48)

        pending_feedbacks = FeedbackMessage.objects.filter(
            statut=FeedbackMessage.Status.PENDING,
            date_creation__gte=cutoff,
        ).select_related('utilisateur')

        count = pending_feedbacks.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Aucun feedback récent à traiter.'))
            return

        subject = f'Nouveaux feedbacks Mi-bika ({count} message(s))'

        lines = []
        for fb in pending_feedbacks:
            lines.append(
                f"- [{fb.get_statut_display()}] {fb.sujet} "
                f"(par {fb.utilisateur.username}, le {fb.date_creation.strftime('%d/%m/%Y %H:%M')})"
            )
            lines.append(f"  Message : {fb.message}")
            lines.append('')

        body = (
            f"Bonjour,\n\n"
            f"{count} nouveau(x) message(s) de feedback a/ont été déposé(s) "
            f"sur Mi-bika depuis les dernières 48 heures.\n\n"
            f"Détails :\n" + "\n".join(lines) + "\n\n"
            f"Ceci est un email automatique généré par la commande "
            f"send_feedback_email.\n"
            f"Date : {now.strftime('%d/%m/%Y %H:%M')}"
        )

        self.stdout.write(f"Sujet : {subject}")
        self.stdout.write(f"Corps :\n{body}")

        recipient_list = getattr(settings, 'FEEDBACK_EMAIL_RECIPIENTS', None)

        if not recipient_list:
            self.stdout.write(
                self.style.WARNING(
                    'FEEDBACK_EMAIL_RECIPIENTS non défini dans settings.py. '
                    'Utilisation de ADMINS par défaut.'
                )
            )
            recipient_list = [admin[1] for admin in settings.ADMINS]

        if not recipient_list:
            self.stdout.write(
                self.style.ERROR(
                    'Aucun destinataire trouvé. '
                    'Veuillez définir FEEDBACK_EMAIL_RECIPIENTS ou ADMINS.'
                )
            )
            return

        self.stdout.write(f"Destinataires : {recipient_list}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING('--dry-run activé : aucun email envoyé.')
            )
            return

        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )
            pending_feedbacks.update(statut=FeedbackMessage.Status.IN_PROGRESS)
            self.stdout.write(
                self.style.SUCCESS(
                    f'{count} email(s) envoyé(s) avec succès à {recipient_list}. '
                    f'Statut mis à jour en IN_PROGRESS.'
                )
            )
        except Exception as e:
            logger.exception('Erreur lors de l\'envoi des emails de feedback')
            self.stderr.write(
                self.style.ERROR(f'Erreur lors de l\'envoi : {e}')
            )