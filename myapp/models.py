from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache


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


# UserProfile ga qo'shimcha maydonlar (oxirgi faollik)
# Migration orqali qo'shiladi — models.py dagi UserProfile ni yangilaymiz
