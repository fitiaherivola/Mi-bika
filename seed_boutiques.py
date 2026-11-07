import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mibika.settings")
django.setup()

from trends.models import Boutique, Tendance

boutiques_data = [
    {
        "nom": "Gasy Style by Rija",
        "description": "Créations artisanales malgaches avec une touche moderne.",
        "style_dominant": "TRADITIONNEL",
        "adresse": "Analakely, Antananarivo",
        "popularite": 85
    },
    {
        "nom": "Urban Mada",
        "description": "Vêtements streetwear pour les jeunes de la capitale.",
        "style_dominant": "CASUAL",
        "adresse": "Tsaralalàna, Antananarivo",
        "popularite": 92
    },
    {
        "nom": "Elégance Tana",
        "description": "Costumes sur mesure et robes de soirée élégantes.",
        "style_dominant": "FORMEL",oir
        "adresse": "Isoraka, Antananarivo",
        "popularite": 78
    },
    {
        "nom": "Fit Mada",
        "description": "Tenues de sport confortables adaptées au climat.",
        "style_dominant": "SPORT",
        "adresse": "Ankorondrano, Antananarivo",
        "popularite": 65
    },
    {
        "nom": "Soa et Belle",
        "description": "Robes de soirée et tenues pour grands événements.",
        "style_dominant": "SOIREE",
        "adresse": "Ambatonakanga, Antananarivo",
        "popularite": 88
    },
    {
        "nom": "Malgache Authentique",
        "description": "Vêtements en lamba landy traditionnels.",
        "style_dominant": "TRADITIONNEL",
        "adresse": "Pavillons Analakely, Antananarivo",
        "popularite": 95
    },
    {
        "nom": "Everyday Chill",
        "description": "Tenues décontractées pour le week-end.",
        "style_dominant": "CASUAL",
        "adresse": "Akoor Digue, Antananarivo",
        "popularite": 82
    },
    {
        "nom": "Business Tana",
        "description": "Prêt-à-porter professionnel pour cadres.",
        "style_dominant": "FORMEL",
        "adresse": "Ivandry, Antananarivo",
        "popularite": 74
    },
    {
        "nom": "Run & Jump",
        "description": "Équipements et vêtements sportifs.",
        "style_dominant": "SPORT",
        "adresse": "Tanjombato, Antananarivo",
        "popularite": 60
    },
    {
        "nom": "Night Out",
        "description": "Le meilleur pour vos sorties nocturnes en ville.",
        "style_dominant": "SOIREE",
        "adresse": "Antaninarenina, Antananarivo",
        "popularite": 90
    }
]

for b_data in boutiques_data:
    Boutique.objects.get_or_create(
        nom=b_data["nom"],
        defaults={
            "description": b_data["description"],
            "style_dominant": b_data["style_dominant"],
            "adresse": b_data["adresse"],
            "popularite": b_data["popularite"],
        }
    )

print("10 boutiques insérées avec succès !")
