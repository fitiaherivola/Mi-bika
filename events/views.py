from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from users.models import Utilisateur
from .models import Evenement, Notification, Calendrier
from .serializers import EvenementSerializer, NotificationSerializer


class ListeEvenementsView(APIView):
    """
    GET  /api/events/evenements/  → liste les événements
    POST /api/events/evenements/  → crée un événement
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        evenements = Evenement.objects.filter(
            utilisateur=request.user
        ).select_related('tenue_reservee', 'calendrier')
        return Response(EvenementSerializer(evenements, many=True).data)

    def post(self, request):
        serializer = EvenementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        evenement = serializer.save(utilisateur=request.user)
        from events.services.notifications import suggerer_tenues_pour_evenement
        try:
            suggerer_tenues_pour_evenement(evenement)
        except Exception:
            pass  # l'événement est créé même si la garde-robe est vide
        return Response(EvenementSerializer(evenement).data,
                        status=status.HTTP_201_CREATED)


class DetailEvenementView(APIView):
    """
    GET    /api/events/evenements/<id>/ → détail
    PATCH  /api/events/evenements/<id>/ → modifier
    DELETE /api/events/evenements/<id>/ → supprimer
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=request.user)
        except Evenement.DoesNotExist:
            return Response({'erreur': 'Événement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(EvenementSerializer(evt).data)

    def patch(self, request, pk):
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=request.user)
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
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=request.user)
        except Evenement.DoesNotExist:
            return Response({'erreur': 'Événement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        evt.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListeCalendriersView(APIView):
    """GET/POST /api/events/calendriers/"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cals = Calendrier.objects.filter(utilisateur=request.user)
        return Response([
            {'id': c.id, 'nom_calendrier': c.nom_calendrier}
            for c in cals
        ])

    def post(self, request):
        cal = Calendrier.objects.create(
            utilisateur=request.user,
            nom_calendrier=request.data.get('nom_calendrier', 'Mon calendrier'),
            api_source_url=request.data.get('api_source_url'),
        )
        return Response(
            {'id': cal.id, 'nom_calendrier': cal.nom_calendrier},
            status=status.HTTP_201_CREATED,
        )


class DetailCalendrierView(APIView):
    """GET/PATCH/DELETE /api/events/calendriers/<id>/"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def _get_cal(self, request, pk):
        return Calendrier.objects.get(pk=pk, utilisateur=request.user)

    def get(self, request, pk):
        try:
            cal = self._get_cal(request, pk)
        except Calendrier.DoesNotExist:
            return Response({'erreur': 'Calendrier introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({'id': cal.id, 'nom_calendrier': cal.nom_calendrier})

    def delete(self, request, pk):
        try:
            cal = self._get_cal(request, pk)
        except Calendrier.DoesNotExist:
            return Response({'erreur': 'Calendrier introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        cal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListeNotificationsView(APIView):
    """
    GET /api/events/notifications/
    Liste les notifications de l'utilisateur.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from events.services.notifications import (
            verifier_rappels_evenements_pour_utilisateur,
            verifier_alertes_meteo_temps_reel,
        )
        try:
            verifier_rappels_evenements_pour_utilisateur(request.user)
            verifier_alertes_meteo_temps_reel(request.user)
        except Exception:
            pass

        notifs = Notification.objects.filter(
            utilisateur=request.user
        ).order_by('-date_envoi')
        return Response(NotificationSerializer(notifs, many=True).data)


class MarquerLueView(APIView):
    """
    PATCH /api/events/notifications/<id>/lue/
    Marque une notification comme lue.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, utilisateur=request.user)
        except Notification.DoesNotExist:
            return Response({'erreur': 'Notification introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        notif.est_lue = True
        notif.save()
        return Response(NotificationSerializer(notif).data)


class NotificationsPourTypeView(APIView):
    """
    GET /api/events/notifications/by-type/
    Récupère les notifications filtrées par type.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_notif = request.query_params.get('type')
        if not type_notif:
            return Response({'erreur': 'Paramètre type requis.'},
                            status=status.HTTP_400_BAD_REQUEST)

        notifs = Notification.objects.filter(
            utilisateur=request.user,
            type_notif=type_notif
        ).order_by('-date_envoi')
        return Response(NotificationSerializer(notifs, many=True).data)


class NotificationsNonLuesView(APIView):
    """
    GET /api/events/notifications/unread/
    Récupère les notifications non lues.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from events.services.notifications import (
            verifier_rappels_evenements_pour_utilisateur,
            verifier_alertes_meteo_temps_reel,
        )
        try:
            verifier_rappels_evenements_pour_utilisateur(request.user)
            verifier_alertes_meteo_temps_reel(request.user)
        except Exception:
            pass

        notifs = Notification.objects.filter(
            utilisateur=request.user,
            est_lue=False
        ).order_by('-date_envoi')
        return Response(NotificationSerializer(notifs, many=True).data)


class GenererTenuePourEvenementView(APIView):
    """
    POST /api/events/evenements/<id>/generer-tenue/
    Génère et associe une tenue adaptée au style/type de l'événement.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            evt = Evenement.objects.get(pk=pk, utilisateur=request.user)
        except Evenement.DoesNotExist:
            return Response({'erreur': 'Événement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)

        from events.services.notifications import suggerer_tenues_pour_evenement
        tenues = suggerer_tenues_pour_evenement(evt, top_k=3)
        if not tenues:
            return Response(
                {'erreur': 'Garde-robe insuffisante pour générer une tenue adaptée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(EvenementSerializer(evt).data, status=status.HTTP_200_OK)
