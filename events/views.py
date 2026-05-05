from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Utilisateur
from .models import Evenement, Notification, Calendrier
from .serializers import EvenementSerializer, NotificationSerializer


def get_utilisateur(request):
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


class ListeEvenementsView(APIView):
    """
    GET  /api/events/evenements/  → liste les événements
    POST /api/events/evenements/  → crée un événement
    """
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        evenements = Evenement.objects.filter(
            utilisateur=utilisateur
        ).select_related('tenue_reservee', 'calendrier')
        return Response(EvenementSerializer(evenements, many=True).data)

    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        serializer = EvenementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        evenement = Evenement.objects.create(
            utilisateur=utilisateur,
            nom_evt=serializer.validated_data.get('nom_evt'),
            date_evt=serializer.validated_data.get('date_evt'),
            lieu=serializer.validated_data.get('lieu'),
            tenue_reservee=serializer.validated_data.get('tenue_reservee'),
            calendrier=serializer.validated_data.get('calendrier'),
        )
        return Response(EvenementSerializer(evenement).data,
                        status=status.HTTP_201_CREATED)


class DetailEvenementView(APIView):
    """
    GET    /api/events/evenements/<id>/ → détail
    PATCH  /api/events/evenements/<id>/ → modifier
    DELETE /api/events/evenements/<id>/ → supprimer
    """
    def get(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=utilisateur)
        except Evenement.DoesNotExist:
            return Response({'erreur': 'Événement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(EvenementSerializer(evt).data)

    def patch(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=utilisateur)
        except Evenement.DoesNotExist:
            return Response({'erreur': 'Événement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = EvenementSerializer(evt, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=utilisateur)
        except Evenement.DoesNotExist:
            return Response({'erreur': 'Événement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        evt.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListeNotificationsView(APIView):
    """
    GET /api/events/notifications/
    Liste les notifications de l'utilisateur.
    """
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        notifs = Notification.objects.filter(
            utilisateur=utilisateur
        ).order_by('-date_envoi')
        return Response(NotificationSerializer(notifs, many=True).data)


class MarquerLueView(APIView):
    """
    PATCH /api/events/notifications/<id>/lue/
    Marque une notification comme lue.
    """
    def patch(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        try:
            notif = Notification.objects.get(pk=pk, utilisateur=utilisateur)
        except Notification.DoesNotExist:
            return Response({'erreur': 'Notification introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        notif.est_lue = True
        notif.save()
        return Response(NotificationSerializer(notif).data)