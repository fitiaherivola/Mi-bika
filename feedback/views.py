from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Utilisateur
from feedback.models import FeedbackMessage
from feedback.serializers import (
    FeedbackMessageSerializer,
    FeedbackMessageUpdateSerializer,
)


def get_utilisateur(request):
    """
    Récupère l'utilisateur depuis l'id passé en paramètre.
    """
    uid = (request.data.get('utilisateur_id')
           or request.query_params.get('utilisateur_id'))
    if not uid:
        return None, Response(
            {'erreur': 'utilisateur_id requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        return Utilisateur.objects.get(pk=uid), None
    except Utilisateur.DoesNotExist:
        return None, Response(
            {'erreur': 'Utilisateur introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )


class FeedbackListView(APIView):
    """
    GET /api/feedback/ — Liste tous les messages de feedback.
    POST /api/feedback/ — Crée un nouveau message de feedback.
    """

    def get(self, request):
        feedbacks = FeedbackMessage.objects.all().order_by('-date_creation')
        serializer = FeedbackMessageSerializer(feedbacks, many=True)
        return Response(serializer.data)

    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        serializer = FeedbackMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        feedback = serializer.save(utilisateur=utilisateur)
        return Response(
            FeedbackMessageSerializer(feedback).data,
            status=status.HTTP_201_CREATED
        )


class FeedbackDetailView(APIView):
    """
    GET /api/feedback/<id>/ — Récupère un message de feedback.
    PATCH /api/feedback/<id>/ — Modifie le statut d'un message de feedback.
    DELETE /api/feedback/<id>/ — Supprime un message de feedback.
    """

    def _get_feedback(self, pk):
        try:
            return FeedbackMessage.objects.get(pk=pk)
        except FeedbackMessage.DoesNotExist:
            return None

    def get(self, request, pk):
        feedback = self._get_feedback(pk)
        if not feedback:
            return Response({'erreur': 'Feedback introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = FeedbackMessageSerializer(feedback)
        return Response(serializer.data)

    def patch(self, request, pk):
        feedback = self._get_feedback(pk)
        if not feedback:
            return Response({'erreur': 'Feedback introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = FeedbackMessageUpdateSerializer(
            feedback, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(FeedbackMessageSerializer(feedback).data)

    def delete(self, request, pk):
        feedback = self._get_feedback(pk)
        if not feedback:
            return Response({'erreur': 'Feedback introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        feedback.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)