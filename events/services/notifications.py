"""
Notifications intelligentes : rappels événements, alertes météo, suggestions de tenues.
"""
from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext as _

from events.models import Evenement, Notification
from events.services.event_style import (
    determiner_style_evenement,
    garde_robe_contient_style,
)
from outfits.services.base import generer_et_sauvegarder_baseline
from outfits.services.optimise import generer_et_sauvegarder_optimise
from weather.services.base import get_meteo_du_jour


def creer_notification(utilisateur, contenu, type_notif, evenement=None):
    return Notification.objects.create(
        utilisateur=utilisateur,
        contenu=contenu,
        type_notif=type_notif,
        evenement=evenement,
    )


def suggerer_tenues_pour_evenement(evenement, top_k=3):
    """
    Génère des tenues anticipées selon le type d'événement et notifie l'utilisateur.
    Si le style cible n'existe pas dans la garde-robe, utilise toute la garde-robe.
    """
    user = evenement.utilisateur
    style_evt = determiner_style_evenement(evenement)
    a_le_style = garde_robe_contient_style(user, style_evt) if style_evt else False

    kwargs = dict(
        utilisateur=user,
        etat='neutre',
        top_k=top_k,
        avec_accessoire=True,
    )
    if a_le_style and style_evt:
        kwargs['styles_autorises'] = [style_evt]

    tenues = generer_et_sauvegarder_optimise(**kwargs)
    if not tenues:
        tenues = generer_et_sauvegarder_baseline(
            utilisateur=user,
            style=style_evt if a_le_style else None,
            top_k=top_k,
        )
    if not tenues:
        return []

    nom = evenement.nom_evt or _('Événement')
    date_str = ''
    if evenement.date_evt:
        date_str = evenement.date_evt.strftime('%d/%m/%Y')

    type_label = evenement.get_type_evt_display() if evenement.type_evt else ''
    style_info = style_evt or _('votre style')
    if not a_le_style and style_evt:
        style_info = _('garde-robe disponible')

    creer_notification(
        utilisateur=user,
        contenu=_(
            'Tenues suggérées pour « %(nom)s » (%(type)s) le %(date)s : '
            '%(count)s proposition(s) (style : %(style)s).'
        ) % {
            'nom': nom,
            'type': type_label or '—',
            'date': date_str or '—',
            'count': len(tenues),
            'style': style_info,
        },
        type_notif=Notification.TypeNotification.TENUE_SUGGEREE,
        evenement=evenement,
    )
    if tenues and not evenement.tenue_reservee:
        evenement.tenue_reservee = tenues[0]
        evenement.save(update_fields=['tenue_reservee'])

    return tenues


def verifier_rappels_evenements():
    """
    Crée des notifications J-3 et J-1 pour les événements à venir (BF9).
    À lancer via : python manage.py send_event_notifications
    """
    now = timezone.now()
    created = 0

    for jours, label in ((3, '3 jours'), (1, 'demain')):
        debut = now + timedelta(days=jours - 1)
        fin = now + timedelta(days=jours + 1)
        evenements = Evenement.objects.filter(
            date_evt__gte=debut,
            date_evt__lte=fin,
        ).select_related('utilisateur')

        for evt in evenements:
            existe = Notification.objects.filter(
                utilisateur=evt.utilisateur,
                evenement=evt,
                contenu__icontains=label,
            ).exists()
            if existe:
                continue

            nom = evt.nom_evt or _('votre événement')
            creer_notification(
                utilisateur=evt.utilisateur,
                contenu=_('Rappel : « %(nom)s » dans %(label)s.') % {
                    'nom': nom, 'label': label
                },
                type_notif=Notification.TypeNotification.EVENEMENT,
                evenement=evt,
            )
            created += 1

    return created


def verifier_rappels_evenements_pour_utilisateur(user):
    """
    Vérifie les événements à venir de l'utilisateur (J-3, J-1) ainsi que les événements
    imminents ou qui commencent maintenant (dans une marge de 15 minutes avant/après).
    """
    now = timezone.now()
    created = 0

    # 1. Rappels J-3 et J-1
    for jours, label in ((3, '3 jours'), (1, 'demain')):
        debut = now + timedelta(days=jours - 1)
        fin = now + timedelta(days=jours + 1)
        evenements = Evenement.objects.filter(
            utilisateur=user,
            date_evt__gte=debut,
            date_evt__lte=fin,
        )

        for evt in evenements:
            existe = Notification.objects.filter(
                utilisateur=user,
                evenement=evt,
                contenu__icontains=label,
            ).exists()
            if existe:
                continue

            nom = evt.nom_evt or _('votre événement')
            creer_notification(
                utilisateur=user,
                contenu=_('Rappel : « %(nom)s » dans %(label)s.') % {
                    'nom': nom, 'label': label
                },
                type_notif=Notification.TypeNotification.EVENEMENT,
                evenement=evt,
            )
            created += 1

    # 2. Rappel d'événement imminent (commence maintenant/bientôt : -15 min à +5 min)
    debut_imminent = now - timedelta(minutes=15)
    fin_imminent = now + timedelta(minutes=5)
    evenements_imminents = Evenement.objects.filter(
        utilisateur=user,
        date_evt__gte=debut_imminent,
        date_evt__lte=fin_imminent,
    )

    for evt in evenements_imminents:
        existe = Notification.objects.filter(
            utilisateur=user,
            evenement=evt,
            contenu__icontains='commence maintenant',
        ).exists()
        if existe:
            continue

        nom = evt.nom_evt or _('votre événement')
        creer_notification(
            utilisateur=user,
            contenu=_('C\'est l\'heure ! « %(nom)s » commence maintenant ! ✨') % {
                'nom': nom
            },
            type_notif=Notification.TypeNotification.EVENEMENT,
            evenement=evt,
        )
        created += 1

    return created


def verifier_alertes_meteo(ville='Antananarivo'):
    """
    Alerte si conditions défavorables (pluie, froid) pour les utilisateurs actifs.
    """
    meteo = get_meteo_du_jour(ville)
    if not meteo:
        return 0

    condition = (meteo.condition or '').lower()
    if not any(m in condition for m in ('rain', 'pluie', 'storm', 'froid', 'cold')):
        return 0

    from users.models import Utilisateur

    created = 0
    for user in Utilisateur.objects.filter(is_active=True)[:100]:
        existe = Notification.objects.filter(
            utilisateur=user,
            type_notif=Notification.TypeNotification.METEO,
            date_envoi__date=timezone.now().date(),
        ).exists()
        if existe:
            continue
        creer_notification(
            utilisateur=user,
            contenu=_(
                'Météo à %(ville)s : %(cond)s (%(temp)s°C). Pensez à adapter votre tenue.'
            ) % {
                'ville': ville,
                'cond': meteo.condition,
                'temp': meteo.temperature,
            },
            type_notif=Notification.TypeNotification.METEO,
        )
        created += 1
    return created


def verifier_alertes_meteo_temps_reel(user):
    """
    Vérifie en temps réel la météo pour les localisations des événements de l'utilisateur sous 24h
    ou pour sa ville par défaut (Antananarivo) en cas de changement climatique soudain.
    """
    from weather.services.openmeteo import sync_weather_for_city
    from weather.services.base import get_meteo_du_jour, get_derniere_meteo
    from weather.models import Meteo

    now = timezone.now()
    villes_a_verifier = set()

    # 1. Trouver les villes des événements de l'utilisateur sous 24h
    debut_24h = now
    fin_24h = now + timedelta(hours=24)
    evenements = Evenement.objects.filter(
        utilisateur=user,
        date_evt__gte=debut_24h,
        date_evt__lte=fin_24h
    )
    for evt in evenements:
        if evt.lieu and evt.lieu.strip():
            villes_a_verifier.add(evt.lieu.strip())

    # Si aucun événement, on vérifie la ville par défaut
    if not villes_a_verifier:
        villes_a_verifier.add("Antananarivo")

    created = 0
    for ville in villes_a_verifier:
        # Éviter de spammer l'utilisateur : max 1 alerte météo par ville toutes les 4 heures
        existe_alerte_recente = Notification.objects.filter(
            utilisateur=user,
            type_notif=Notification.TypeNotification.METEO,
            contenu__icontains=ville,
            date_envoi__gte=now - timedelta(hours=4)
        ).exists()
        if existe_alerte_recente:
            continue

        # Récupérer la météo avant sync pour détecter le changement soudain
        meteo_avant = Meteo.objects.filter(ville__iexact=ville).order_by('-id').first()

        # Synchroniser la météo en temps réel
        try:
            sync_weather_for_city(ville)
        except Exception:
            pass

        # Récupérer la nouvelle météo
        meteo_apres = get_meteo_du_jour(ville) or get_derniere_meteo(ville)
        if not meteo_apres:
            continue

        condition = (meteo_apres.condition or '').lower()
        temp = meteo_apres.temperature

        sudden_change = False
        if meteo_avant and meteo_avant.condition != meteo_apres.condition:
            sudden_change = True

        is_bad_weather = any(m in condition for m in ('rain', 'pluie', 'storm', 'orage', 'froid', 'cold'))

        # Si mauvais temps, changement soudain, ou si c'est la première alerte météo de la journée
        should_notify = is_bad_weather or sudden_change or not Notification.objects.filter(
            utilisateur=user,
            type_notif=Notification.TypeNotification.METEO,
            date_envoi__date=now.date()
        ).exists()

        if should_notify:
            if is_bad_weather:
                contenu = _(
                    "🚨 Attention météo à %(ville)s : %(cond)s (%(temp)s°C). Pensez à adapter votre tenue !"
                ) % {'ville': ville, 'cond': meteo_apres.condition, 'temp': temp}
            elif sudden_change:
                contenu = _(
                    "⚠️ Changement climatique soudain à %(ville)s : c'est désormais %(cond)s (%(temp)s°C). Pensez à adapter votre tenue !"
                ) % {'ville': ville, 'cond': meteo_apres.condition, 'temp': temp}
            else:
                contenu = _(
                    "🌤️ Météo du jour à %(ville)s : %(cond)s (%(temp)s°C). Passez une excellente journée !"
                ) % {'ville': ville, 'cond': meteo_apres.condition, 'temp': temp}

            creer_notification(
                utilisateur=user,
                contenu=contenu,
                type_notif=Notification.TypeNotification.METEO
            )
            created += 1

    return created
