from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone


class UserProfile(models.Model):
    RACE_CHOICES = [
        ('elf', 'Elflar'),
        ('human', 'Odamlar'),
        ('dwarf', 'Gnomlar'),
        ('hobbit', 'Xobbitlar'),
        ('ent', 'Entlar'),
        ('ainur', 'Aynurlar'),
        ('orc', 'Orklar'),
        ('uruk_hai', 'Uruk-xaylar'),
        ('troll', 'Trollar'),
        ('dragon', 'Ajdaholar'),
        ('warg', 'Varglar'),
    ]

    FACTION_CHOICES = [
        ('gondor', 'Gondor'),
        ('rohan', 'Rohan'),
        ('rivendell', 'Rivendell'),
        ('lothlorien', 'Lothlorien'),
        ('woodland_realm', 'Woodland Realm'),
        ('erebor', 'Erebor'),
        ('mordor', 'Mordor'),
        ('isengard', 'Isengard'),
        ('goblin', 'Goblinlar'),
    ]

    # Fraksiya ro'yxati tanlangan irqga qarab filtrlanadi.
    RACE_FACTIONS = {
        'elf': ('rivendell', 'lothlorien', 'woodland_realm'),
        'human': ('gondor', 'rohan'),
        'dwarf': ('erebor',),
        'orc': ('mordor', 'isengard', 'goblin'),
        'uruk_hai': ('mordor', 'isengard'),
        'troll': ('mordor', 'goblin'),
        'dragon': ('mordor',),
        'warg': ('mordor', 'isengard', 'goblin'),
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.CharField(max_length=200, blank=True)
    favorite_race = models.CharField(max_length=20, choices=RACE_CHOICES, blank=True)
    faction = models.CharField(max_length=30, choices=FACTION_CHOICES, blank=True)
    is_banned = models.BooleanField(default=False, verbose_name="Bloklangan")
    ban_reason = models.CharField(max_length=255, blank=True, verbose_name="Blok sababi")
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Oxirgi faollik")
    reputation = models.IntegerField(default=0, verbose_name="Obro'")
    is_moderator = models.BooleanField(default=False, verbose_name="Moderator")

    class Meta:
        verbose_name = "Foydalanuvchi profili"
        verbose_name_plural = "Foydalanuvchi profillari"

    def __str__(self):
        return f"{self.user.username} profili"

    def display_race(self):
        return dict(self.RACE_CHOICES).get(self.favorite_race, self.favorite_race or '—')

    def display_faction(self):
        return dict(self.FACTION_CHOICES).get(self.faction, self.faction or '—')


class ChatMessage(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    STICKER = 'sticker'
    TYPE_CHOICES = [
        (TEXT, 'Matn'),
        (IMAGE, 'Rasm'),
        (STICKER, 'Stiker'),
    ]

    name = models.CharField(max_length=60, verbose_name="Ism")
    text = models.TextField(max_length=500, blank=True, verbose_name="Matn")
    message_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=TEXT, verbose_name="Turi"
    )
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True, verbose_name="Rasm")
    sticker = models.CharField(max_length=10, blank=True, verbose_name="Stiker")
    is_hidden = models.BooleanField(default=False, verbose_name="Yashirilgan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat xabari"
        verbose_name_plural = "Chat xabarlari"

    def __str__(self):
        return f"{self.name}: {self.text[:30] if self.text else self.message_type}"


class Faction(models.Model):
    slug = models.SlugField(unique=True, help_text="URL uchun (masalan: gondor)")
    name = models.CharField(max_length=100, verbose_name="Nomi")
    color = models.CharField(max_length=20, default='#c9a34e', help_text="HEX rang, masalan #c9a34e")
    icon = models.CharField(max_length=10, default='👑', verbose_name="Emoji ikonka")
    tagline = models.CharField(max_length=200, blank=True, verbose_name="Qisqa shior")
    symbol = models.CharField(max_length=100, blank=True, verbose_name="Ramz")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    traits = models.TextField(
        blank=True,
        help_text="Har bir xususiyatni yangi qatorda yozing",
        verbose_name="Xususiyatlar",
    )
    ruler_name = models.CharField(max_length=100, blank=True, verbose_name="Hukmdor nomi")
    ruler_title = models.CharField(max_length=100, blank=True, verbose_name="Hukmdor unvoni")
    ruler_image = models.ImageField(
        upload_to='factions/', null=True, blank=True, verbose_name="Hukmdor rasmi"
    )
    castle_name = models.CharField(max_length=100, blank=True, verbose_name="Qal'a nomi")
    castle_image = models.ImageField(
        upload_to='factions/', null=True, blank=True, verbose_name="Qal'a rasmi"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Fraksiya"
        verbose_name_plural = "Fraksiyalar"

    def __str__(self):
        return self.name

    def get_traits_list(self):
        if not self.traits:
            return []
        return [t.strip() for t in self.traits.splitlines() if t.strip()]


class Character(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ism")
    title = models.CharField(max_length=150, blank=True, verbose_name="Unvon / lavozim")
    icon = models.CharField(max_length=10, default='⚔', verbose_name="Emoji")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    race = models.CharField(max_length=50, blank=True, verbose_name="Xalq / irq")
    image = models.ImageField(upload_to='characters/', null=True, blank=True, verbose_name="Rasm")
    is_featured = models.BooleanField(default=True, verbose_name="Bosh sahifada ko'rsatish")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Qahramon"
        verbose_name_plural = "Qahramonlar"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    subtitle = models.CharField(max_length=200, blank=True, verbose_name="Qisqa tavsif")
    part_number = models.PositiveSmallIntegerField(default=1, verbose_name="Qism raqami")
    pdf_file = models.FileField(
        upload_to='books/', null=True, blank=True, verbose_name="PDF fayl"
    )
    cover_image = models.ImageField(
        upload_to='books/covers/', null=True, blank=True, verbose_name="Muqova"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")

    class Meta:
        ordering = ['order', 'part_number']
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"

    def __str__(self):
        return f"{self.part_number}. {self.title}"


class MapLocation(models.Model):
    LOCATION_TYPES = [
        ('region', 'Hudud'),
        ('city', 'Shahar'),
        ('fortress', "Qal'a"),
        ('forest', "O'rmon"),
        ('mountain', "Tog'"),
        ('other', 'Boshqa'),
    ]

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100, verbose_name="Nomi")
    region = models.CharField(max_length=100, blank=True, verbose_name="Hudud")
    location_type = models.CharField(
        max_length=20, choices=LOCATION_TYPES, default='region', verbose_name="Turi"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")
    population = models.CharField(max_length=100, blank=True, verbose_name="Aholi")
    landmarks = models.TextField(
        blank=True,
        help_text="Diqqatga sazovor joylar (har birini yangi qatorda)",
        verbose_name="Diqqatga sazovor joylar",
    )
    image = models.ImageField(
        upload_to='locations/', null=True, blank=True, verbose_name="Rasm"
    )
    pos_x = models.FloatField(default=50, verbose_name="X pozitsiya (%)")
    pos_y = models.FloatField(default=50, verbose_name="Y pozitsiya (%)")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Xarita joyi"
        verbose_name_plural = "Xarita joylari"

    def __str__(self):
        return self.name

    def get_landmarks_list(self):
        if not self.landmarks:
            return []
        return [t.strip() for t in self.landmarks.splitlines() if t.strip()]


class SiteSetting(models.Model):
    """Yagona sozlamalar yozuvi (singleton)."""
    site_title = models.CharField(
        max_length=200, default="Uzuklar Hukmdori", verbose_name="Sayt nomi"
    )
    site_tagline = models.CharField(
        max_length=300, blank=True, default="O'rta Yer haqidagi afsona", verbose_name="Shior"
    )
    hero_text = models.TextField(blank=True, verbose_name="Bosh sahifa matni")
    footer_text = models.TextField(blank=True, verbose_name="Footer matni")
    chat_enabled = models.BooleanField(default=True, verbose_name="Muhokama yoqilgan")
    gandalf_enabled = models.BooleanField(default=True, verbose_name="Gandalf yoqilgan")
    registration_enabled = models.BooleanField(default=True, verbose_name="Ro'yxatdan o'tish yoqilgan")
    game_download_enabled = models.BooleanField(default=True, verbose_name="O'yin yuklash yoqilgan")
    maintenance_mode = models.BooleanField(default=False, verbose_name="Texnik ishlar rejimi")
    maintenance_message = models.TextField(
        blank=True,
        default="Sayt vaqtincha texnik ishlar tufayli yopiq. Tez orada qaytamiz!",
        verbose_name="Texnik ishlar xabari",
    )
    max_chat_message_length = models.PositiveIntegerField(default=500, verbose_name="Max xabar uzunligi")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sayt sozlamasi"
        verbose_name_plural = "Sayt sozlamalari"

    def __str__(self):
        return "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('site_settings')

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj = cache.get('site_settings')
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set('site_settings', obj, 300)
        return obj


class BannedWord(models.Model):
    word = models.CharField(max_length=100, unique=True, verbose_name="So'z")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['word']
        verbose_name = "Taqiqlangan so'z"
        verbose_name_plural = "Taqiqlangan so'zlar"

    def __str__(self):
        return self.word


class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    body = models.TextField(verbose_name="Matn")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    starts_at = models.DateTimeField(null=True, blank=True, verbose_name="Boshlanish")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Tugash")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "E'lon"
        verbose_name_plural = "E'lonlar"

    def __str__(self):
        return self.title


# ==================== HAMJAMIYAT / FORUM ====================

class ForumCategory(models.Model):
    """Forum bo'limlari — masalan: Umumiy, Fraksiyalar, Kitoblar, O'yinlar."""
    name = models.CharField(max_length=100, verbose_name="Nomi")
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, blank=True, verbose_name="Tavsif")
    icon = models.CharField(max_length=10, default='📜', verbose_name="Ikonka")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Forum bo'limi"
        verbose_name_plural = "Forum bo'limlari"

    def __str__(self):
        return f"{self.icon} {self.name}"

    def topic_count(self):
        return self.topics.filter(is_hidden=False).count()


class Topic(models.Model):
    """Forum mavzusi."""
    category = models.ForeignKey(
        ForumCategory, on_delete=models.CASCADE, related_name='topics', verbose_name="Bo'lim"
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='topics', verbose_name="Muallif"
    )
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    body = models.TextField(max_length=5000, verbose_name="Matn")
    is_pinned = models.BooleanField(default=False, verbose_name="Qadalgan")
    is_locked = models.BooleanField(default=False, verbose_name="Yopilgan")
    is_hidden = models.BooleanField(default=False, verbose_name="Yashirilgan")
    views = models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        verbose_name = "Mavzu"
        verbose_name_plural = "Mavzular"

    def __str__(self):
        return self.title

    def reply_count(self):
        return self.posts.filter(is_hidden=False).count()

    def last_post(self):
        return self.posts.filter(is_hidden=False).order_by('-created_at').first()


class Post(models.Model):
    """Mavzuga javob (post)."""
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='posts', verbose_name="Mavzu"
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='forum_posts', verbose_name="Muallif"
    )
    body = models.TextField(max_length=5000, verbose_name="Matn")
    is_hidden = models.BooleanField(default=False, verbose_name="Yashirilgan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Javob"
        verbose_name_plural = "Javoblar"

    def __str__(self):
        return f"{self.author} — {self.topic.title[:40]}"


# ==================== REKLAMA ====================

class Advertisement(models.Model):
    """Reklama banneri — admin panel orqali to'liq boshqariladi."""

    PLACEMENT_CHOICES = [
        ('side', "Yon banner (chap yoki o'ng, doim ko'rinadi)"),
        ('index_middle', "Bosh sahifa — bo'limlar orasida"),
        ('footer', "Footer tepasi (barcha sahifalar, pastda)"),
    ]

    SIDE_CHOICES = [
        ('left', "Chap tomon"),
        ('right', "O'ng tomon"),
    ]

    BANNER_STYLE_CHOICES = [
        ('1', "1 — Klassik uchli"),
        ('2', "2 — Ayri dumli (lasttochka)"),
        ('3', "3 — To'lqinli chekka"),
        ('4', "4 — Bayroqcha (qiya uchli)"),
        ('5', "5 — Qalqon shakli"),
        ('6', "6 — Lenta (tasma, ikki uchli)"),
        ('7', "7 — Gotik uchli"),
    ]

    title = models.CharField(
        max_length=150, verbose_name="Ichki nom",
        help_text="Faqat admin panelda ko'rinadi (masalan: 'Yangi yil aksiyasi').",
    )
    image = models.ImageField(upload_to='ads/', verbose_name="Banner rasmi")
    url = models.URLField(
        max_length=500, blank=True, verbose_name="Havola (URL)",
        help_text="Bosilganda foydalanuvchi shu manzilga o'tadi. Bo'sh qoldirilsa, banner bosilmaydigan bo'ladi.",
    )
    placement = models.CharField(
        max_length=20, choices=PLACEMENT_CHOICES, default='side', verbose_name="Joylashuvi",
    )
    side = models.CharField(
        max_length=5, choices=SIDE_CHOICES, default='right', verbose_name="Tomoni",
        help_text="Faqat 'Yon banner' joylashuvi uchun ishlaydi — chap yoki o'ng chekkada chiqadi.",
    )
    banner_style = models.CharField(
        max_length=2, choices=BANNER_STYLE_CHOICES, default='1', verbose_name="Banner shakli",
        help_text="Fraksiya bannerlari uslubidagi 7 xil shakldan biri — faqat 'Yon banner' uchun.",
    )
    open_new_tab = models.BooleanField(default=True, verbose_name="Yangi oynada ochilsin")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    starts_at = models.DateTimeField(null=True, blank=True, verbose_name="Boshlanish vaqti")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Tugash vaqti")
    click_count = models.PositiveIntegerField(default=0, verbose_name="Bosilganlar soni", editable=False)
    view_count = models.PositiveIntegerField(default=0, verbose_name="Ko'rsatilganlar soni", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['placement', 'order', '-created_at']
        verbose_name = "Reklama"
        verbose_name_plural = "Reklamalar"

    def __str__(self):
        return f"{self.title} ({self.get_placement_display()})"

    def is_currently_active(self):
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at < now:
            return False
        return True

    def ctr(self):
        """Click-through rate (%) — ko'rsatilganlarga nisbatan bosilganlar."""
        if not self.view_count:
            return 0
        return round((self.click_count / self.view_count) * 100, 2)


# UserProfile ga qo'shimcha maydonlar (oxirgi faollik)
# Migration orqali qo'shiladi — models.py dagi UserProfile ni yangilaymiz


# ==================== SUPPORT CENTER ====================

class SupportTicket(models.Model):
    CATEGORY_BUG = 'bug'
    CATEGORY_SUGGESTION = 'suggestion'
    CATEGORY_REPORT_USER = 'report_user'
    CATEGORY_ACCOUNT = 'account'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_BUG, '🐛 Bug Report'),
        (CATEGORY_SUGGESTION, '💡 Suggestion'),
        (CATEGORY_REPORT_USER, '⚠ Report User'),
        (CATEGORY_ACCOUNT, '🔒 Account Problem'),
        (CATEGORY_OTHER, '❓ Other'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_CLOSED, 'Closed'),
    ]

    ticket_number = models.PositiveIntegerField(
        unique=True, editable=False, verbose_name="Ticket №"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='support_tickets',
        verbose_name="Foydalanuvchi",
    )
    subject = models.CharField(max_length=200, verbose_name="Mavzu")
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER,
        verbose_name="Kategoriya",
    )
    description = models.TextField(max_length=5000, verbose_name="Tavsif")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM,
        verbose_name="Muhimlik",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN,
        verbose_name="Holat",
    )
    attachment = models.FileField(
        upload_to='support/tickets/', blank=True, null=True,
        verbose_name="Ilova (screenshot / fayl)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="Yopilgan")

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Support ticket"
        verbose_name_plural = "Support ticketlar"

    def __str__(self):
        return f"Ticket #{self.ticket_number} — {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last = (
                SupportTicket.objects.order_by('-ticket_number')
                .values_list('ticket_number', flat=True)
                .first()
            )
            self.ticket_number = (last or 1000) + 1
        super().save(*args, **kwargs)

    def status_badge(self):
        return {
            self.STATUS_OPEN: ('🟢', 'Open', '#3d8b5a'),
            self.STATUS_IN_PROGRESS: ('🟡', 'In Progress', '#c9a34e'),
            self.STATUS_CLOSED: ('🔴', 'Closed', '#b53a3a'),
        }.get(self.status, ('⚪', self.status, '#888'))

    def display_number(self):
        return f"Ticket #{self.ticket_number}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name='messages',
        verbose_name="Ticket",
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='ticket_messages',
        verbose_name="Muallif",
    )
    body = models.TextField(max_length=3000, blank=True, verbose_name="Xabar")
    attachment = models.FileField(
        upload_to='support/messages/', blank=True, null=True,
        verbose_name="Fayl",
    )
    is_staff_reply = models.BooleanField(default=False, verbose_name="Admin javobi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Ticket xabari"
        verbose_name_plural = "Ticket xabarlari"

    def __str__(self):
        who = self.author.username if self.author else '—'
        return f"{who}: {(self.body or '[fayl]')[:40]}"


class SupportTeamMember(models.Model):
    """Sayt adminlari, developerlari va support xodimlari — admin paneldan boshqariladi."""

    ROLE_DEVELOPER = 'developer'
    ROLE_ADMIN = 'admin'
    ROLE_SUPPORT = 'support'
    ROLE_CHOICES = [
        (ROLE_DEVELOPER, '🛠 Developer'),
        (ROLE_ADMIN, '⚔ Site Admin'),
        (ROLE_SUPPORT, '📜 Support'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='support_team',
        verbose_name="Foydalanuvchi",
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=ROLE_SUPPORT,
        verbose_name="Lavozim",
    )
    title = models.CharField(
        max_length=120, blank=True,
        verbose_name="Unvon",
        help_text="Masalan: Bosh dasturchi, Moderator, Support agent",
    )
    bio = models.CharField(max_length=300, blank=True, verbose_name="Qisqa bio")
    link_url = models.URLField(
        max_length=500, blank=True,
        verbose_name="Havola (URL)",
        help_text="Kartaga bosilganda ochiladigan sahifa (Telegram, GitHub, profil va h.k.).",
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    show_on_page = models.BooleanField(
        default=True, verbose_name="Jamoa sahifasida ko'rsatish",
    )
    can_manage_tickets = models.BooleanField(
        default=True,
        verbose_name="Ticketlarni boshqara oladi",
        help_text="Yoqilsa, ushbu a'zo support ticketlarga javob bera oladi (staff bo'lmasa ham).",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'role', 'user__username']
        verbose_name = "Support jamoa a'zosi"
        verbose_name_plural = "Support jamoa"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def display_title(self):
        return self.title or self.get_role_display()


def user_can_manage_tickets(user):
    """Staff/superuser yoki faol support jamoa a'zosi (can_manage_tickets=True)."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_staff or user.is_superuser:
        return True
    try:
        member = user.support_team
        return bool(member.is_active and member.can_manage_tickets)
    except Exception:
        return False
