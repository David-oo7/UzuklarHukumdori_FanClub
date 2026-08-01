from django.utils import timezone

from .models import Announcement, SiteSetting


def site_extras(request):
    """Barcha template'larga e'lonlar, sayt sozlamalari va foydalanuvchi irqini beradi."""
    now = timezone.now()
    announcements = (
        Announcement.objects.filter(is_active=True)
        .filter(
            # starts_at bo'sh yoki o'tgan; ends_at bo'sh yoki kelajak
        )
    )
    # Vaqt filtri
    active = []
    for a in announcements:
        if a.starts_at and a.starts_at > now:
            continue
        if a.ends_at and a.ends_at < now:
            continue
        active.append(a)

    try:
        settings_obj = SiteSetting.load()
    except Exception:
        settings_obj = None

    # Foydalanuvchi irqi (tema uchun) + last_seen yangilash
    user_race = ''
    user_faction = ''
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            user_race = profile.favorite_race or ''
            user_faction = profile.faction or ''
            if not profile.last_seen or (now - profile.last_seen).total_seconds() > 300:
                profile.last_seen = now
                profile.save(update_fields=['last_seen'])
        except Exception:
            user_race = ''

    return {
        'announcements': active,
        'site_settings': settings_obj,
        'user_race': user_race,
        'user_faction': user_faction,
    }
