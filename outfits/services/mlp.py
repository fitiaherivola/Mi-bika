"""
Mini réseau de neurones (MLP) — prédiction des préférences utilisateur.
Algorithme n°8 du cahier des charges Mi-bika.

Architecture : 28 entrées → 16 neurones cachés (ReLU) → 1 sortie (sigmoid)
Entraînement : descente de gradient sur l'historique des notations.
"""
import math
import random

from outfits.models import Tenue
from outfits.services.knn import vectoriser_tenue
from ratings.models import Notation


def _sigmoid(x):
    x = max(-500, min(500, x))
    return 1.0 / (1.0 + math.exp(-x))


def _relu(x):
    return max(0.0, x)


class MLPPreference:
    """
    Perceptron multicouche léger — implémentation manuelle (sans numpy/sklearn).
    """

    def __init__(self, input_size=28, hidden_size=16, seed=42):
        random.seed(seed)
        self.input_size = input_size
        self.hidden_size = hidden_size
        # Poids W1 [hidden x input], b1 [hidden], W2 [1 x hidden], b2 [1]
        scale1 = math.sqrt(2.0 / input_size)
        scale2 = math.sqrt(2.0 / hidden_size)
        self.W1 = [
            [random.uniform(-scale1, scale1) for _ in range(input_size)]
            for _ in range(hidden_size)
        ]
        self.b1 = [0.0] * hidden_size
        self.W2 = [random.uniform(-scale2, scale2) for _ in range(hidden_size)]
        self.b2 = 0.0

    def forward(self, x):
        hidden = []
        for j in range(self.hidden_size):
            s = self.b1[j]
            for i in range(self.input_size):
                s += self.W1[j][i] * x[i]
            hidden.append(_relu(s))

        out = self.b2
        for j in range(self.hidden_size):
            out += self.W2[j] * hidden[j]
        return _sigmoid(out), hidden

    def train(self, X, y, epochs=80, lr=0.05):
        """Entraîne le MLP sur des paires (vecteur, note normalisée 0-1)."""
        n = len(X)
        if n == 0:
            return

        for _ in range(epochs):
            for idx in range(n):
                x, target = X[idx], y[idx]
                pred, hidden = self.forward(x)
                error = pred - target

                # Rétropropagation sortie
                for j in range(self.hidden_size):
                    grad = error * hidden[j] * pred * (1 - pred)
                    self.W2[j] -= lr * grad
                self.b2 -= lr * error * pred * (1 - pred)

                # Couche cachée
                for j in range(self.hidden_size):
                    if hidden[j] <= 0:
                        continue
                    delta_h = error * self.W2[j] * pred * (1 - pred)
                    for i in range(self.input_size):
                        self.W1[j][i] -= lr * delta_h * x[i]
                    self.b1[j] -= lr * delta_h

    def predict(self, x):
        pred, _ = self.forward(x)
        return round(pred * 100, 2)


def _charger_donnees_entrainement(utilisateur):
    notations = Notation.objects.filter(
        utilisateur=utilisateur,
    ).select_related('tenue', 'tenue__haut', 'tenue__bas', 'tenue__accessoire')

    X, y = [], []
    for n in notations:
        if not n.tenue:
            continue
        X.append(vectoriser_tenue(n.tenue))
        y.append(n.note / 5.0)
    return X, y


def entrainer_mlp_utilisateur(utilisateur) -> MLPPreference | None:
    X, y = _charger_donnees_entrainement(utilisateur)
    if len(X) < 2:
        return None
    mlp = MLPPreference()
    mlp.train(X, y)
    return mlp


def predire_score_tenue(utilisateur, tenue: Tenue) -> float | None:
    mlp = entrainer_mlp_utilisateur(utilisateur)
    if not mlp:
        return None
    return mlp.predict(vectoriser_tenue(tenue))


def recommander_tenues_mlp(utilisateur, top_k=5) -> list:
    """
    Classe les tenues de l'utilisateur par score MLP prédit.
    """
    mlp = entrainer_mlp_utilisateur(utilisateur)
    if not mlp:
        return []

    tenues = Tenue.objects.filter(utilisateur=utilisateur).select_related(
        'haut', 'bas', 'accessoire'
    )
    scores = []
    for t in tenues:
        scores.append((mlp.predict(vectoriser_tenue(t)), t))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            'tenue': t,
            'score_mlp': s,
            'algorithme': 'mlp',
        }
        for s, t in scores[:top_k]
    ]
