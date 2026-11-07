import json

from django.test import TestCase, Client

from users.models import Utilisateur
from wardrobe.models import Vetement, Contrainte
from outfits.models import Tenue


class OutfitGenerationAPITest(TestCase):
    """Tests API garde-robe et génération de tenues."""

    def setUp(self):
        self.client = Client()
        self.user = Utilisateur.objects.create_user(
            username='outfit_test_user',
            password='testpass123',
        )
        self.client.force_login(self.user)
        self.items_payload = [
            {
                "nom": "T-shirt Blanc",
                "categorie": "HAUT",
                "couleur_hex": "#FFFFFF",
                "saison": "ETE",
                "style": "CASUAL",
                "est_propre": True,
            },
            {
                "nom": "Jean Bleu",
                "categorie": "BAS",
                "couleur_hex": "#0000FF",
                "saison": "ETE",
                "style": "CASUAL",
                "est_propre": True,
            },
            {
                "nom": "Chapeau Jaune",
                "categorie": "ACCESSOIRE",
                "couleur_hex": "#FFFF00",
                "saison": "ETE",
                "style": "CASUAL",
                "est_propre": True,
            },
        ]
        for item in self.items_payload:
            response = self.client.post(
                '/api/wardrobe/',
                data=json.dumps(item),
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 201, response.content)

    def test_wardrobe_list(self):
        response = self.client.get('/api/wardrobe/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_baseline_generation(self):
        response = self.client.post(
            '/api/outfits/generer/baseline/',
            data=json.dumps({"top_k": 2}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.json()), 0)

    def test_optimise_after_baseline(self):
        """La génération optimisée doit fonctionner même après une baseline."""
        self.client.post(
            '/api/outfits/generer/baseline/',
            data=json.dumps({"top_k": 2}),
            content_type='application/json',
        )
        response = self.client.post(
            '/api/outfits/generer/optimise/',
            data=json.dumps({
                "saison": "ETE",
                "humeur": "heureuse",
                "condition_meteo": "ensoleille",
                "saison_actuelle": "ETE",
                "top_k": 2,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertGreater(len(response.json()), 0)

    def test_api_endpoints_responsive(self):
        for endpoint in ['/api/wardrobe/', '/api/outfits/', '/api/events/']:
            response = self.client.get(endpoint)
            self.assertLess(response.status_code, 500, endpoint)

    def test_generation_performance_under_2s(self):
        """BNF1 : génération baseline < 2 secondes."""
        import time
        start = time.perf_counter()
        response = self.client.post(
            '/api/outfits/generer/baseline/',
            data=json.dumps({"top_k": 3}),
            content_type='application/json',
        )
        elapsed = time.perf_counter() - start
        self.assertEqual(response.status_code, 201)
        self.assertLess(elapsed, 2.0, f'Génération trop lente: {elapsed:.2f}s')

    def test_palette_couleurs(self):
        response = self.client.get('/api/wardrobe/palette/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()['couleurs']), 10)

    def test_jwt_login(self):
        response = self.client.post(
            '/api/users/login/',
            data=json.dumps({
                'username': 'outfit_test_user',
                'password': 'testpass123',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('jwt_access', data)
        self.assertIn('jwt_refresh', data)
