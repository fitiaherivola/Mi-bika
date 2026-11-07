from django.test import TestCase
from django.contrib.auth import get_user_model
from feedback.models import FeedbackMessage


User = get_user_model()


class FeedbackMessageModelTest(TestCase):

    def setUp(self):
        self.utilisateur = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_creation_feedback(self):
        """Test la création d'un message de feedback."""
        feedback = FeedbackMessage.objects.create(
            sujet='Test sujet',
            message='Test message',
            utilisateur=self.utilisateur
        )
        self.assertEqual(str(feedback), '[En attente] Test sujet — testuser')
        self.assertEqual(feedback.statut, FeedbackMessage.Status.PENDING)
        self.assertEqual(feedback.get_statut_display(), 'En attente')

    def test_statuts_disponibles(self):
        """Test que tous les statuts sont disponibles."""
        self.assertEqual(FeedbackMessage.Status.PENDING, 'PENDING')
        self.assertEqual(FeedbackMessage.Status.IN_PROGRESS, 'IN_PROGRESS')
        self.assertEqual(FeedbackMessage.Status.RESOLVED, 'RESOLVED')

    def test_ordering(self):
        """Test que les feedbacks sont ordonnés par date_creation décroissante."""
        old = FeedbackMessage.objects.create(
            sujet='Ancien',
            message='Message ancien',
            utilisateur=self.utilisateur
        )
        import django.utils.timezone as tz
        from django.utils import timezone
        newer = FeedbackMessage.objects.create(
            sujet='Nouveau',
            message='Message nouveau',
            utilisateur=self.utilisateur
        )
        self.assertGreater(newer.date_creation, old.date_creation)

    def test_meta_db_table(self):
        """Test que le db_table est correct."""
        self.assertEqual(FeedbackMessage._meta.db_table, 'feedback_message')