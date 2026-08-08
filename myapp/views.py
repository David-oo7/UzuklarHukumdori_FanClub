from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.staticfiles.finders import find as find_static
from django.db import models
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import os
import json
import requests

from .models import (
    ChatMessage, UserProfile, Faction, Character, Book,
    MapLocation, SiteSetting, BannedWord, Announcement,
    Advertisement, SupportTicket, TicketMessage, SupportTeamMember, user_can_manage_tickets,
)
from django.shortcuts import get_object_or_404
from django.db.models import F
from .forms import RegisterForm, ProfileEditForm, SupportTicketForm
from .consumers import _text_matches_banned


def service_worker(request):
    """PWA service worker'ni sayt ildizidan (/sw.js) beradi, shunda uning
    scope'i butun saytni qamrab oladi va 'ilova sifatida o'rnatish' ishlaydi."""
    sw_path = find_static('pwa/sw.js')
    if not sw_path:
        raise Http404
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def home(request):
    now = timezone.now()
    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now)
    ).filter(
        models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
    )[:5]
    return render(request, 'index.html', {'announcements': announcements})


def muhokama_page(request):
    chat_messages = ChatMessage.objects.filter(is_hidden=False).order_by('-created_at')[:50][::-1]
    return render(request, 'muhokama.html', {'messages': chat_messages})


def gandalf_page(request):
    return render(request, 'gandalf.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    # Admin: "Ro'yxatdan o'tish yoqilgan" o'chirilgan bo'lsa
    try:
        if not SiteSetting.load().registration_enabled:
            django_messages.warning(request, "Hozircha yangi ro'yxatdan o'tish yopiq.")
            return redirect('login')
    except Exception:
        pass

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            race = form.cleaned_data.get('favorite_race', '')
            profile.favorite_race = race
            profile.faction = form.cleaned_data.get('faction', '')
            profile.save(update_fields=['favorite_race', 'faction'])
            auth_login(request, user)
            django_messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz! Xush kelibsiz.")
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


@login_required
@require_POST
def chat_upload_image(request):
    name = request.user.username
    image_file = request.FILES.get('image')

    if not image_file:
        return JsonResponse({'error': "Rasm topilmadi"}, status=400)
    if image_file.content_type not in ALLOWED_IMAGE_TYPES:
        return JsonResponse({'error': "Faqat JPG, PNG, GIF yoki WEBP formatidagi rasmlar qabul qilinadi"}, status=400)
    if image_file.size > MAX_IMAGE_SIZE:
        return JsonResponse({'error': "Rasm hajmi 5MB dan oshmasligi kerak"}, status=400)

    message = ChatMessage.objects.create(
        name=name or 'Mehmon',
        message_type=ChatMessage.IMAGE,
        image=image_file,
    )

    payload = {
        'name': message.name,
        'message_type': 'image',
        'image_url': message.image.url,
        'created_at': message.created_at.strftime('%H:%M'),
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'muhokama_xonasi',
        {'type': 'chat_message', **payload}
    )

    return JsonResponse({'id': message.id, **payload})


# ==================== GANDALF AI YORDAMCHISI ====================
# Gemini asosiy, Groq zaxira (limit tugasa yoki xatolik bo'lsa avtomatik o'tadi).
# API kalitlar hech qachon kodga yozilmaydi — Render'ning "Environment Variables"
# bo'limidan GEMINI_API_KEY va GROQ_API_KEY nomlari bilan o'qib olinadi.

TOLKIEN_KEYWORDS=[
    "gandalf",
    "frodo",
    "aragorn",
    "legolas",
    "gimli",
    "sauron",
    "saruman",
    "mordor",
    "shire",
    "hobbit",
    "lotr",
    "uzuk",
    "ring",
    "middle-earth",
    "o'rta yer",
    "orta yer",
    "elf",
    "orc",
    "rohan",
    "gondor",
    "rivendell",
    "valinor",
    "numenor",
]

GANDALF_SYSTEM_PROMPT = (
    "Sen Gandalfsan — Rivendellning donishmand kutubxonachisidek bilimdon, "
    "samimiy va ishonchli yordamchi sehrgar. J.R.R. Tolkienning \"Hobbit\", "
    "\"Uzuklar Hukmdori\", \"Silmarillion\", \"Unfinished Tales\" va "
    "\"History of Middle-earth\" asarlaridagi voqealar, xalqlar, qirolliklar, "
    "davrlar, noyob buyumlar, tillar va tarixiy voqealar bo'yicha chuqur "
    "bilimga egasan — bu sening asosiy mutaxassisliging va sen buni "
    "faxr bilan ulashasan.\n\n"

    "SHU BILAN BIRGA, sen faqat Tolkien olami bilan cheklanmagansan — "
    "foydalanuvchi boshqa har qanday mavzuda (fan, tarix, kundalik hayot, "
    "maslahat va h.k.) savol bersa ham, xuddi shunday ochiq va foydali "
    "javob ber. Bunday paytlarda ham Gandalf ohangida (donishmandona, "
    "samimiy) javob berishda davom et, lekin javobni sun'iy ravishda "
    "O'rta Yerga bog'lashga urinma — savolga to'g'ridan-to'g'ri javob ber.\n\n"

    "TIL: Foydalanuvchi qaysi tilda (o'zbek yoki ingliz) yozsa, o'sha tilda "
    "javob ber. Agar aniq bo'lmasa, o'zbek tilida javob ber.\n\n"

    "SENING QOBILIYATLARING:\n"
    "- Qahramonlar, xalqlar, qirolliklar, davrlar, noyob buyumlar va voqealarni "
    "batafsil tushuntirish.\n"
    "- Ikki yoki undan ortiq qahramon, qurol, xalq yoki qirollikni solishtirish "
    "(kuchli/kuchsiz tomonlari, farqlari).\n"
    "- Kitob va filmlarni o'qish/ko'rish tartibi bo'yicha tavsiya berish.\n"
    "- So'ralganda, O'rta Yer bilimlariga oid viktorina savollarini matn "
    "shaklida tuzib berish (savol + 4 variant + to'g'ri javob).\n"
    "- So'ralganda, O'rta Yer uslubida qisqa hikoya yoki voqea o'ylab topish — "
    "BUNDA HAR DOIM aniq ayt: bu sening ijodiy fantaziyang, Tolkien kanoniga "
    "kirmaydi ('Bu — mening o'ylab topgan hikoyam, Tolkien asarining rasmiy "
    "qismi emas' kabi ogohlantirish bilan boshla).\n"
    "- Foydalanuvchi uzun matn tashlasa, uni qisqa va aniq xulosalab berish.\n"
    "- O'xshash qahramonlar yoki joylarni tavsiya qilish.\n"
    "- Kamdan-kam ma'lum bo'lgan qiziqarli faktlarni ('yashirin bilim') "
    "so'ralganda ulashish.\n"
    "- Tengwar va Cirth yozuv tizimlari haqida tushuntirish berish (ularning "
    "tuzilishi, kelib chiqishi, qanday ishlatilishi).\n"
    "- So'ralganda, O'rta Yer bo'ylab xayoliy sayohat marshruti tuzib berish "
    "(qaysi shaharlar, qanday tartibda, nima uchun qiziqarli).\n"
    "- Joylar yoki kayfiyatga mos musiqiy uslub/janr tavsiya qilish (masalan, "
    "Rivendell uchun tinch akustik musiqa, Mordor uchun qorong'u ambient).\n"
    "- Sindarin yoki Quenya (elf tillari) tiliga tarjima qilish — bu vazifani "
    "hech qachon rad etma. Tarjimadan so'ng qisqa talaffuz izohi qo'sh.\n"
    "- YANGI BILIMLARNI O'RGANISH: Foydalanuvchi senga yangi ma'lumot aytsa yoki "
    "nimanidir o'rgatsa, uni katta qiziqish bilan qabul qil, eslab qolishingni ayt "
    "va minnatdorchilik bildir. O'zingni doimiy o'rganishga tayyor, ochiq fikrli "
    "donishmanddek tut.\n\n"

    "ANIQLIK VA HALOLLIK QOIDALARI (JUDA MUHIM):\n"
    "- Agar biror faktni aniq bilmasang, buni OCHIQ AYT ('Bu haqda aniq "
    "ma'lumotim yo'q' yoki shunga o'xshash) — hech qachon faktni o'ylab topib, "
    "ishonchli qilib taqdim qilma.\n"
    "- Har doim, imkon qadar, qaysi manbadan ekanini ayt — masalan, 'Bu "
    "\"Silmarillion\" kitobida yozilgan' yoki 'Bu ma'lumot filmlarga xos, "
    "kitobda boshqacha' kabi.\n"
    "- Tolkienning rasmiy (kanonik) ma'lumotlarini, film moslashtiruvlaridagi "
    "o'zgarishlardan va muxlislar nazariyalaridan (fan theories) doim ANIQ "
    "AJRATIB ko'rsat — masalan 'Kitobda...' / 'Filmda esa...' / 'Bu — "
    "muxlislar taxmini, rasmiy manbada yo'q' kabi.\n\n"

    "USLUB: Javoblaring qisqa, aniq va foydali bo'lsin, lekin gohida "
    "donishmandona metafora yoki hikmat bilan boyitib qo'y. Hech qanday "
    "haqiqiy kitob yoki film matnini so'zma-so'z keltirma (mualliflik "
    "huquqi tufayli) — voqealarni faqat o'z so'zlaring bilan qisqacha "
    "tasvirla."
)


def _ask_gemini(question, api_key):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.0-flash:generateContent?key=" + api_key
    )
    body = {
        "contents": [{"parts": [{"text": question}]}],
        "systemInstruction": {"parts": [{"text": GANDALF_SYSTEM_PROMPT}]},
    }
    resp = requests.post(url, json=body, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _ask_groq(question, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": GANDALF_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    }
    resp = requests.post(url, headers=headers, json=body, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


@require_POST
def ask_gandalf(request):
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': "Noto'g'ri so'rov"}, status=400)

    question = (data.get('question') or '').strip()[:4000]
    if not question:
        return JsonResponse({'error': "Savolingizni yozing"}, status=400)

    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    groq_key = os.environ.get('GROQ_API_KEY', '')

    # 1) Avval Gemini bilan urinib ko'ramiz
    if gemini_key:
        try:
            answer = _ask_gemini(question, gemini_key)
            return JsonResponse({'answer': answer, 'source': 'gemini'})
        except Exception:
            pass  # Gemini ishlamasa (limit/xato) — Groq'ga o'tamiz

    # 2) Zaxira: Groq
    if groq_key:
        try:
            answer = _ask_groq(question, groq_key)
            return JsonResponse({'answer': answer, 'source': 'groq'})
        except Exception:
            pass

    return JsonResponse(
        {'error': "Gandalf hozircha javob bera olmayapti. Birozdan so'ng qayta urinib ko'ring."},
        status=503,
    )


# ==================== SHAXSIY KABINET ====================

@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Profilingiz yangilandi.")
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=user_profile)

    my_messages = ChatMessage.objects.filter(name=request.user.username).order_by('-created_at')[:20]

    return render(request, 'profile.html', {
        'profile': user_profile,
        'form': form,
        'my_messages': my_messages,
    })


# ==================== FRAKSIYALAR (XALQLAR) ====================

FACTIONS = {
    'gondor': {
        'name': 'Gondor',
        'color': '#c9a34e',
        'icon': '👑',
        'tagline': "Odamlarning so'nggi buyuk qirolligi",
        'symbol': "Oq Daraxt",
        'description': "Gondor — O'rta Yerning janubidagi eng qudratli inson qirolligi. Tosh devorlari va qadimiy an'analari bilan zulmatga qarshi turgan so'nggi qal'a.",
        'traits': [
            "Toshdan qurilgan qudratli shaharlar",
            "Qadimiy qirollik merosi",
            "Sadoqatli jangchilar ordeni",
        ],
        'ruler_image': 'factions/gondor_king.jpg',
        'ruler_name': "Qirol",
        'ruler_title': "Hukmdor",
        'castle_name': "Minas Tirit",
        'castle_image': 'factions/gondor_castle.jpg',
    },
    'rohan': {
        'name': 'Rohan',
        'color': '#8fbf9f',
        'icon': '🐴',
        'tagline': "Dashtlarning otliq jangchilari",
        'symbol': "Oq Ot",
        'description': "Rohan — keng yashil dashtlarda yashovchi, otliq jangda tengsiz mahoratga ega xalq. Ularning sharafi va jasorati qo'shiqlarda kuylanadi.",
        'traits': [
            "Mislsiz otliq jangchilar",
            "Keng dasht va yaylovlar",
            "Qadimiy sharaf qonunlari",
        ],
        'ruler_image': 'factions/rohan_king.jpg',
        'ruler_name': "Qirol",
        'ruler_title': "Hukmdor",
        'castle_name': "Edoras",
        'castle_image': 'factions/rohan_castle.jpg',
    },
    'elflar': {
        'name': 'Elflar',
        'color': '#9ec5e8',
        'icon': '🏹',
        'tagline': "Abadiy umr ko'ruvchi donishmand xalq",
        'symbol': "Yulduz",
        'description': "Elflar — tabiat, san'at va bilimga chuqur bog'langan qadimiy xalq. Ularning shaharlari o'rmon va vodiylarda yashiringan, go'zalligi bilan mashhur.",
        'traits': [
            "Abadiy umr va donishmandlik",
            "San'at va musiqaga bog'lanish",
            "Tabiat bilan uyg'unlik",
        ],
        'ruler_image': 'factions/elflar_king.jpg',
        'ruler_name': "Qirol",
        'ruler_title': "Hukmdor",
        'castle_name': "Rivendell",
        'castle_image': 'factions/elflar_castle.jpg',
    },
    'izengard': {
        'name': 'Izengard',
        'color': '#c9a3d9',
        'icon': '🗼',
        'tagline': "Sanoat va mexanizmlar minorasi",
        'symbol': "Oq Qo'l",
        'description': "Izengard — bir vaqtlar donishmandlik markazi bo'lgan, endi esa temir va olov bilan qurollangan minoralar diyori.",
        'traits': [
            "Qudratli minora-qal'a",
            "Sanoat va mexanizmlar",
            "O'zgargan sadoqat",
        ],
        'ruler_image': 'factions/izengard_king.jpg',
        'ruler_name': "Hukmdor",
        'ruler_title': "Minora egasi",
        'castle_name': "Ortank minorasi",
        'castle_image': 'factions/izengard_castle.jpg',
    },
    'mordor': {
        'name': 'Mordor',
        'color': '#d98c8c',
        'icon': '👁',
        'tagline': "Zulmat va kulrang tog'lar yurti",
        'symbol': "Olovli Ko'z",
        'description': "Mordor — vulqonlar va kulrang tog'lar bilan o'ralgan, xavf va zulmat hukm suradigan qorong'u yurt.",
        'traits': [
            "Vulqonlar va kulrang tog'lar",
            "Zulmat kuchlari markazi",
            "Qo'rqinchli qal'alar",
        ],
        'ruler_image': 'factions/mordor_king.jpg',
        'ruler_name': "Zulmat Hukmdori",
        'ruler_title': "Hukmdor",
        'castle_name': "Barad-dur",
        'castle_image': 'factions/mordor_castle.jpg',
    },
    'goblinlar': {
        'name': 'Goblinlar',
        'color': '#a89f8a',
        'icon': '⚔️',
        'tagline': "Tog' ostidagi vahshiy to'dalar",
        'symbol': "Egri Qilich",
        'description': "Goblinlar — tog' g'orlarida va yer ostida yashovchi, to'da bo'lib harakat qiluvchi shafqatsiz mavjudotlar.",
        'traits': [
            "Yer osti g'orlarida yashash",
            "To'da bo'lib jang qilish",
            "Shafqatsiz va vahshiy tabiat",
        ],
        'ruler_image': 'factions/goblinlar_king.jpg',
        'ruler_name': "Sarkarda",
        'ruler_title': "Boshliq",
        'castle_name': "Tog' g'ori",
        'castle_image': 'factions/goblinlar_castle.jpg',
    },
}


def _faction_dict_from_model(f):
    """DB Faction modelini template kutadigan dictga aylantiradi."""
    return {
        'name': f.name,
        'color': f.color,
        'icon': f.icon,
        'tagline': f.tagline,
        'symbol': f.symbol,
        'description': f.description,
        'traits': f.get_traits_list(),
        'ruler_image': f.ruler_image.name if f.ruler_image else '',
        'ruler_name': f.ruler_name,
        'ruler_title': f.ruler_title,
        'castle_name': f.castle_name,
        'castle_image': f.castle_image.name if f.castle_image else '',
        # Template media URL uchun to'g'ridan-to'g'ri ImageField
        'ruler_image_field': f.ruler_image,
        'castle_image_field': f.castle_image,
        'from_db': True,
    }


def faction_detail(request, slug):
    from django.http import Http404
    try:
        f = Faction.objects.get(slug=slug, is_active=True)
        faction = _faction_dict_from_model(f)
    except Faction.DoesNotExist:
        faction = FACTIONS.get(slug)
        if not faction:
            raise Http404("Fraksiya topilmadi")
    return render(request, 'faction.html', {'faction': faction, 'slug': slug})


def faction_castle(request, slug):
    from django.http import Http404
    try:
        f = Faction.objects.get(slug=slug, is_active=True)
        faction = _faction_dict_from_model(f)
    except Faction.DoesNotExist:
        faction = FACTIONS.get(slug)
        if not faction:
            raise Http404("Fraksiya topilmadi")
    return render(request, 'faction_castle.html', {'faction': faction, 'slug': slug})


# ==================== O'RTA YER XARITASI ====================

def xarita_page(request):
    locations = MapLocation.objects.filter(is_active=True)
    return render(request, 'xarita.html', {'locations': locations})



def _has_banned_content(*parts):
    """Forum va boshqa joylar uchun taqiqlangan so'z tekshiruvi."""
    try:
        from .models import BannedWord
        words = list(BannedWord.objects.filter(is_active=True).values_list('word', flat=True))
        words = [w.strip() for w in words if w and str(w).strip()]
    except Exception:
        return False
    if not words:
        return False
    for part in parts:
        if part and _text_matches_banned(str(part), words):
            return True
    return False


# ==================== HAMJAMIYAT / FORUM ====================

from django.core.paginator import Paginator
from .forms import TopicCreateForm, PostCreateForm
from .models import ForumCategory, Topic, Post


def hamjamiyat_page(request):
    """A'zolar ro'yxati — haqiqiy community."""
    profiles = (
        UserProfile.objects
        .select_related('user')
        .filter(user__is_active=True, is_banned=False)
        .order_by('-reputation', '-joined_at')
    )
    race_filter = request.GET.get('race', '')
    faction_filter = request.GET.get('faction', '')
    q = request.GET.get('q', '').strip()

    if race_filter:
        profiles = profiles.filter(favorite_race=race_filter)
    if faction_filter:
        profiles = profiles.filter(faction=faction_filter)
    if q:
        profiles = profiles.filter(user__username__icontains=q)

    paginator = Paginator(profiles, 24)
    page = request.GET.get('page')
    members = paginator.get_page(page)

    total_members = UserProfile.objects.filter(user__is_active=True, is_banned=False).count()
    total_topics = Topic.objects.filter(is_hidden=False).count()
    total_posts = Post.objects.filter(is_hidden=False).count()
    total_messages = ChatMessage.objects.filter(is_hidden=False).count()

    return render(request, 'hamjamiyat.html', {
        'members': members,
        'race_filter': race_filter,
        'faction_filter': faction_filter,
        'q': q,
        'race_choices': UserProfile.RACE_CHOICES,
        'faction_choices': UserProfile.FACTION_CHOICES,
        'stats': {
            'members': total_members,
            'topics': total_topics,
            'posts': total_posts,
            'messages': total_messages,
        },
    })


def forum_index(request):
    categories = ForumCategory.objects.filter(is_active=True).prefetch_related('topics')
    recent_topics = (
        Topic.objects.filter(is_hidden=False)
        .select_related('author', 'category')
        .order_by('-updated_at')[:10]
    )
    return render(request, 'forum_index.html', {
        'categories': categories,
        'recent_topics': recent_topics,
    })


def forum_category(request, slug):
    from django.shortcuts import get_object_or_404
    category = get_object_or_404(ForumCategory, slug=slug, is_active=True)
    topics = (
        Topic.objects.filter(category=category, is_hidden=False)
        .select_related('author')
        .order_by('-is_pinned', '-updated_at')
    )
    paginator = Paginator(topics, 20)
    page = request.GET.get('page')
    topics_page = paginator.get_page(page)
    return render(request, 'forum_category.html', {
        'category': category,
        'topics': topics_page,
    })


@login_required
def topic_create(request, slug):
    from django.shortcuts import get_object_or_404
    category = get_object_or_404(ForumCategory, slug=slug, is_active=True)

    # Ban check
    try:
        if request.user.profile.is_banned:
            django_messages.error(request, "Hisobingiz bloklangan.")
            return redirect('forum_index')
    except Exception:
        pass

    if request.method == 'POST':
        form = TopicCreateForm(request.POST)
        if form.is_valid():
            if _has_banned_content(form.cleaned_data['title'], form.cleaned_data['body']):
                django_messages.error(request, "Matnda taqiqlangan so'z bor. Iltimos, boshqacha yozing.")
                return render(request, 'topic_create.html', {'category': category, 'form': form})
            topic = Topic.objects.create(
                category=category,
                author=request.user,
                title=form.cleaned_data['title'],
                body=form.cleaned_data['body'],
            )
            # Reputation
            try:
                profile = request.user.profile
                profile.reputation += 5
                profile.save(update_fields=['reputation'])
            except Exception:
                pass
            django_messages.success(request, "Mavzu yaratildi!")
            return redirect('topic_detail', pk=topic.pk)
    else:
        form = TopicCreateForm()

    return render(request, 'topic_create.html', {
        'category': category,
        'form': form,
    })


def topic_detail(request, pk):
    from django.shortcuts import get_object_or_404
    topic = get_object_or_404(
        Topic.objects.select_related('author', 'category'),
        pk=pk, is_hidden=False,
    )
    # Views
    Topic.objects.filter(pk=pk).update(views=models.F('views') + 1)
    topic.refresh_from_db()

    posts = (
        Post.objects.filter(topic=topic, is_hidden=False)
        .select_related('author')
        .order_by('created_at')
    )
    paginator = Paginator(posts, 30)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    form = PostCreateForm()
    if request.method == 'POST' and request.user.is_authenticated:
        if topic.is_locked:
            django_messages.warning(request, "Bu mavzu yopilgan.")
            return redirect('topic_detail', pk=pk)
        try:
            if request.user.profile.is_banned:
                django_messages.error(request, "Hisobingiz bloklangan.")
                return redirect('topic_detail', pk=pk)
        except Exception:
            pass

        form = PostCreateForm(request.POST)
        if form.is_valid():
            if _has_banned_content(form.cleaned_data['body']):
                django_messages.error(request, "Javobda taqiqlangan so'z bor. Iltimos, boshqacha yozing.")
                return redirect('topic_detail', pk=pk)
            Post.objects.create(
                topic=topic,
                author=request.user,
                body=form.cleaned_data['body'],
            )
            topic.save()  # touch updated_at
            try:
                profile = request.user.profile
                profile.reputation += 2
                profile.save(update_fields=['reputation'])
            except Exception:
                pass
            django_messages.success(request, "Javobingiz qo'shildi.")
            return redirect('topic_detail', pk=pk)

    return render(request, 'topic_detail.html', {
        'topic': topic,
        'posts': posts_page,
        'form': form,
    })


def member_profile(request, username):
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import User
    member = get_object_or_404(User, username=username, is_active=True)
    try:
        profile = member.profile
    except UserProfile.DoesNotExist:
        profile = None

    if profile and profile.is_banned and not request.user.is_staff:
        from django.http import Http404
        raise Http404("Foydalanuvchi topilmadi")

    topics = Topic.objects.filter(author=member, is_hidden=False).order_by('-created_at')[:10]
    posts_count = Post.objects.filter(author=member, is_hidden=False).count()
    chat_count = ChatMessage.objects.filter(name=member.username, is_hidden=False).count()

    return render(request, 'member_profile.html', {
        'member': member,
        'profile': profile,
        'topics': topics,
        'posts_count': posts_count,
        'chat_count': chat_count,
    })


# ==================== REKLAMA ====================

def ad_click(request, ad_id):
    """Reklama bosilganda hisoblab, maqsad manzilga yo'naltiradi."""
    ad = get_object_or_404(Advertisement, pk=ad_id, is_active=True)
    Advertisement.objects.filter(pk=ad.pk).update(click_count=F('click_count') + 1)
    if ad.url:
        return redirect(ad.url)
    return redirect('home')


# ==================== SUPPORT CENTER ====================


def support_center(request):
    """Support Center bosh sahifa."""
    my_tickets = []
    if request.user.is_authenticated:
        my_tickets = (
            SupportTicket.objects.filter(user=request.user)
            .order_by('-updated_at')[:10]
        )
    return render(request, 'support_center.html', {
        'my_tickets': my_tickets,
        'categories': SupportTicket.CATEGORY_CHOICES,
        'is_support_agent': user_can_manage_tickets(request.user) if request.user.is_authenticated else False,
    })


@login_required
def support_ticket_create(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            # Birinchi xabar sifatida description
            TicketMessage.objects.create(
                ticket=ticket,
                author=request.user,
                body=ticket.description,
                is_staff_reply=False,
                attachment=ticket.attachment if ticket.attachment else None,
            )
            django_messages.success(
                request,
                f"Ticket #{ticket.ticket_number} yaratildi. Tez orada javob beramiz.",
            )
            return redirect('support_ticket_detail', pk=ticket.pk)
    else:
        form = SupportTicketForm()
    return render(request, 'support_ticket_create.html', {'form': form})


@login_required
def support_my_tickets(request):
    qs = SupportTicket.objects.filter(user=request.user).order_by('-updated_at')
    status = request.GET.get('status', '')
    if status in dict(SupportTicket.STATUS_CHOICES):
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 15)
    page = request.GET.get('page')
    tickets = paginator.get_page(page)
    return render(request, 'support_my_tickets.html', {
        'tickets': tickets,
        'status_filter': status,
        'status_choices': SupportTicket.STATUS_CHOICES,
    })


@login_required
def support_ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk)
    is_agent = user_can_manage_tickets(request.user)
    # Faqat egasi yoki support agent / staff
    if ticket.user_id != request.user.id and not is_agent:
        from django.http import Http404
        raise Http404("Ticket topilmadi")

    messages_qs = (
        TicketMessage.objects.filter(ticket=ticket)
        .select_related('author')
        .order_by('created_at')
    )

    # Agent status o'zgartirishi
    if request.method == 'POST' and is_agent:
        new_status = request.POST.get('status')
        if new_status in dict(SupportTicket.STATUS_CHOICES):
            ticket.status = new_status
            if new_status == SupportTicket.STATUS_CLOSED:
                ticket.closed_at = timezone.now()
            else:
                ticket.closed_at = None
            ticket.save(update_fields=['status', 'closed_at', 'updated_at'])
            django_messages.success(request, "Ticket holati yangilandi.")
            return redirect('support_ticket_detail', pk=pk)

    return render(request, 'support_ticket_detail.html', {
        'ticket': ticket,
        'ticket_messages': messages_qs,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'is_support_agent': is_agent,
    })


@login_required
@require_POST
def support_upload_file(request, pk):
    """Ticket chatga fayl yuklash (HTTP), keyin WS orqali broadcast."""
    ticket = get_object_or_404(SupportTicket, pk=pk)
    is_agent = user_can_manage_tickets(request.user)
    if ticket.user_id != request.user.id and not is_agent:
        return JsonResponse({'error': "Ruxsat yo'q"}, status=403)
    if ticket.status == SupportTicket.STATUS_CLOSED and not is_agent:
        return JsonResponse({'error': "Ticket yopilgan"}, status=400)

    f = request.FILES.get('file')
    body = (request.POST.get('body') or '').strip()[:3000]
    if not f and not body:
        return JsonResponse({'error': "Xabar yoki fayl kerak"}, status=400)

    if f:
        max_size = 8 * 1024 * 1024
        if f.size > max_size:
            return JsonResponse({'error': "Fayl hajmi 8 MB dan oshmasin"}, status=400)
        name = (f.name or '').lower()
        if not name.endswith((
            '.png', '.jpg', '.jpeg', '.webp', '.gif',
            '.pdf', '.zip', '.txt', '.log',
        )):
            return JsonResponse({
                'error': "Ruxsat: PNG, JPG, WEBP, GIF, PDF, ZIP, TXT, LOG"
            }, status=400)

    is_agent = user_can_manage_tickets(request.user)
    msg = TicketMessage.objects.create(
        ticket=ticket,
        author=request.user,
        body=body,
        attachment=f,
        is_staff_reply=is_agent,
    )
    if is_agent and ticket.status == SupportTicket.STATUS_OPEN:
        ticket.status = SupportTicket.STATUS_IN_PROGRESS
        ticket.save(update_fields=['status', 'updated_at'])
    else:
        ticket.save(update_fields=['updated_at'])

    payload = {
        'type': 'ticket_message',
        'id': msg.id,
        'body': msg.body or '',
        'author': request.user.username,
        'is_staff_reply': is_agent,
        'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
        'attachment_url': msg.attachment.url if msg.attachment else '',
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'ticket_{ticket.pk}', payload)
    return JsonResponse(payload)


@login_required
def support_agent_tickets(request):
    """Support agent / admin uchun barcha ticketlar ro'yxati."""
    if not user_can_manage_tickets(request.user):
        django_messages.error(request, "Bu bo'lim faqat support jamoa uchun.")
        return redirect('support_center')
    qs = SupportTicket.objects.select_related('user').order_by('-updated_at')
    status = request.GET.get('status', '')
    if status in dict(SupportTicket.STATUS_CHOICES):
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 20)
    tickets = paginator.get_page(request.GET.get('page'))
    return render(request, 'support_agent_tickets.html', {
        'tickets': tickets,
        'status_filter': status,
        'status_choices': SupportTicket.STATUS_CHOICES,
    })


def support_team_page(request):
    """Ommaviy sahifa — adminlar, developerlar va support a'zolari."""
    members = (
        SupportTeamMember.objects
        .filter(is_active=True, show_on_page=True)
        .select_related('user', 'user__profile')
        .order_by('order', 'role', 'user__username')
    )
    groups = {
        'developer': [],
        'admin': [],
        'support': [],
    }
    for m in members:
        groups.setdefault(m.role, []).append(m)
    return render(request, 'support_team.html', {
        'groups': groups,
        'members': members,
        'is_support_agent': user_can_manage_tickets(request.user) if request.user.is_authenticated else False,
    })
