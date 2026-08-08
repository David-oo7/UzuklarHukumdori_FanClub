from django.utils import timezone
from django.db.models import F

from .models import Announcement, SiteSetting, Advertisement


def site_extras(request):
    """Barcha template'larga e'lonlar, sayt sozlamalari, reklamalar va foydalanuvchi irqini beradi."""
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

    # Reklama bannerlari (joylashuvi bo'yicha guruhlangan)
    is_home_page = getattr(request.resolver_match, 'url_name', None) == 'home'
    ads_by_placement = {'side': [], 'index_middle': [], 'footer': []}
    ad_ids_to_count = []
    for ad in Advertisement.objects.filter(is_active=True):
        if ad.starts_at and ad.starts_at > now:
            continue
        if ad.ends_at and ad.ends_at < now:
            continue
        ads_by_placement.setdefault(ad.placement, []).append(ad)
        # index_middle faqat bosh sahifada ko'rinadi — shu yerda hisoblanadi
        if ad.placement == 'index_middle' and not is_home_page:
            continue
        ad_ids_to_count.append(ad.pk)

    # Yon banner — har tomondan faqat bittadan (tartib bo'yicha birinchisi) chiqadi
    side_ads = ads_by_placement.get('side', [])
    ad_side_left = next((a for a in side_ads if a.side == 'left'), None)
    ad_side_right = next((a for a in side_ads if a.side == 'right'), None)

    if ad_ids_to_count:
        Advertisement.objects.filter(pk__in=ad_ids_to_count).update(
            view_count=F('view_count') + 1
        )

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
        'ad_side_left': ad_side_left,
        'ad_side_right': ad_side_right,
        'ads_index_middle': ads_by_placement.get('index_middle', []),
        'ads_footer': ads_by_placement.get('footer', []),
    }
