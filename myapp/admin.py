from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    UserProfile,
    ChatMessage,
    Faction,
    Character,
    Book,
    MapLocation,
    SiteSetting,
    BannedWord,
    Announcement,
    ForumCategory,
    Topic,
    Post,
)


# ─── Helper: rasm preview ───────────────────────────────────────────────────

def _img_preview(field, max_h=80):
    if field and hasattr(field, 'url'):
        try:
            return format_html(
                '<img src="{}" style="max-height:{}px;border-radius:6px;" />',
                field.url,
                max_h,
            )
        except Exception:
            return "—"
    return "—"


# ─── User + Profile ─────────────────────────────────────────────────────────

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profil"
    fk_name = 'user'
    fields = (
        'avatar', 'bio', 'favorite_race', 'faction',
        'is_banned', 'ban_reason', 'is_moderator', 'reputation',
        'joined_at', 'last_seen',
    )
    readonly_fields = ('joined_at', 'last_seen')


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'is_staff', 'is_active',
        'profile_banned', 'date_joined', 'last_login',
    )
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined', 'profile__is_banned')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['ban_users', 'unban_users', 'activate_users', 'deactivate_users']

    @admin.display(description="Blok", boolean=True)
    def profile_banned(self, obj):
        try:
            return obj.profile.is_banned
        except UserProfile.DoesNotExist:
            return False

    @admin.action(description="Tanlanganlarni bloklash")
    def ban_users(self, request, queryset):
        count = 0
        for u in queryset:
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.is_banned = True
            profile.ban_reason = profile.ban_reason or "Admin tomonidan bloklangan"
            profile.save(update_fields=['is_banned', 'ban_reason'])
            count += 1
        self.message_user(request, f"{count} foydalanuvchi bloklandi.", messages.SUCCESS)

    @admin.action(description="Blokni olib tashlash")
    def unban_users(self, request, queryset):
        count = 0
        for u in queryset:
            try:
                u.profile.is_banned = False
                u.profile.ban_reason = ""
                u.profile.save(update_fields=['is_banned', 'ban_reason'])
                count += 1
            except UserProfile.DoesNotExist:
                pass
        self.message_user(request, f"{count} foydalanuvchi blokdan chiqarildi.", messages.SUCCESS)

    @admin.action(description="Faollashtirish")
    def activate_users(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"{n} foydalanuvchi faollashtirildi.", messages.SUCCESS)

    @admin.action(description="Faolsizlantirish")
    def deactivate_users(self, request, queryset):
        n = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"{n} foydalanuvchi faolsizlantirildi.", messages.WARNING)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'avatar_preview', 'favorite_race', 'faction',
        'reputation', 'is_moderator', 'is_banned', 'joined_at', 'message_count',
    )
    list_filter = ('favorite_race', 'faction', 'is_banned', 'is_moderator', 'joined_at')
    search_fields = ('user__username', 'user__email', 'bio')
    readonly_fields = ('joined_at', 'last_seen', 'avatar_preview')
    list_editable = ('is_banned', 'is_moderator', 'reputation')
    actions = ['ban_selected', 'unban_selected', 'make_moderator', 'remove_moderator', 'boost_rep']

    fieldsets = (
        (None, {'fields': ('user', 'avatar', 'avatar_preview', 'bio', 'favorite_race', 'faction')}),
        ('Hamjamiyat', {'fields': ('reputation', 'is_moderator', 'last_seen')}),
        ('Bloklash', {'fields': ('is_banned', 'ban_reason')}),
        ('Meta', {'fields': ('joined_at',)}),
    )

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        return _img_preview(obj.avatar, 50)

    @admin.display(description="Xabarlar")
    def message_count(self, obj):
        return ChatMessage.objects.filter(name=obj.user.username).count()

    @admin.action(description="Bloklash")
    def ban_selected(self, request, queryset):
        queryset.update(is_banned=True)
        self.message_user(request, "Tanlanganlar bloklandi.", messages.SUCCESS)

    @admin.action(description="Blokni olib tashlash")
    def unban_selected(self, request, queryset):
        queryset.update(is_banned=False, ban_reason="")
        self.message_user(request, "Blok olib tashlandi.", messages.SUCCESS)

    @admin.action(description="Moderator qilish")
    def make_moderator(self, request, queryset):
        n = queryset.update(is_moderator=True)
        self.message_user(request, f"{n} foydalanuvchi moderator qilindi.", messages.SUCCESS)

    @admin.action(description="Moderatorlikni olib tashlash")
    def remove_moderator(self, request, queryset):
        n = queryset.update(is_moderator=False)
        self.message_user(request, f"{n} moderatorlik olib tashlandi.", messages.WARNING)

    @admin.action(description="+50 obro' berish")
    def boost_rep(self, request, queryset):
        for p in queryset:
            p.reputation += 50
            p.save(update_fields=['reputation'])
        self.message_user(request, f"{queryset.count()} foydalanuvchiga +50 obro' berildi.", messages.SUCCESS)


# ─── Chat ───────────────────────────────────────────────────────────────────

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'message_type', 'text_preview', 'image_preview',
        'is_hidden', 'created_at',
    )
    list_filter = ('message_type', 'is_hidden', 'created_at')
    search_fields = ('name', 'text')
    readonly_fields = ('created_at', 'image_preview')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 50
    list_editable = ('is_hidden',)
    actions = [
        'hide_messages', 'show_messages', 'delete_selected',
        'delete_images_only',
    ]

    fieldsets = (
        (None, {
            'fields': (
                'name', 'message_type', 'text', 'sticker',
                'image', 'image_preview', 'is_hidden', 'created_at',
            )
        }),
    )

    @admin.display(description="Matn")
    def text_preview(self, obj):
        if obj.message_type == 'sticker':
            return obj.sticker
        if obj.message_type == 'image':
            return "[Rasm]"
        return (obj.text[:60] + '…') if len(obj.text) > 60 else obj.text

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        return _img_preview(obj.image, 60)

    @admin.action(description="Yashirish")
    def hide_messages(self, request, queryset):
        n = queryset.update(is_hidden=True)
        self.message_user(request, f"{n} xabar yashirildi.", messages.SUCCESS)

    @admin.action(description="Ko'rsatish")
    def show_messages(self, request, queryset):
        n = queryset.update(is_hidden=False)
        self.message_user(request, f"{n} xabar ko'rsatildi.", messages.SUCCESS)

    @admin.action(description="Faqat rasmlarni o'chirish (xabar qoladi)")
    def delete_images_only(self, request, queryset):
        n = 0
        for msg in queryset.filter(message_type=ChatMessage.IMAGE):
            if msg.image:
                msg.image.delete(save=False)
                msg.image = None
                msg.save(update_fields=['image'])
                n += 1
        self.message_user(request, f"{n} rasm o'chirildi.", messages.SUCCESS)


# ─── Faction ────────────────────────────────────────────────────────────────

@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = (
        'icon_name', 'slug', 'color_swatch', 'is_active',
        'order', 'ruler_name', 'castle_name', 'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'tagline', 'description', 'ruler_name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    list_per_page = 30
    readonly_fields = ('ruler_preview', 'castle_preview', 'created_at', 'updated_at')
    actions = ['activate', 'deactivate']

    fieldsets = (
        ('Asosiy', {
            'fields': ('slug', 'name', 'icon', 'color', 'tagline', 'symbol', 'order', 'is_active'),
        }),
        ('Tavsif', {
            'fields': ('description', 'traits'),
        }),
        ('Hukmdor', {
            'fields': ('ruler_name', 'ruler_title', 'ruler_image', 'ruler_preview'),
        }),
        ("Qal'a", {
            'fields': ('castle_name', 'castle_image', 'castle_preview'),
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description="Fraksiya")
    def icon_name(self, obj):
        return f"{obj.icon} {obj.name}"

    @admin.display(description="Rang")
    def color_swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:24px;height:24px;'
            'background:{};border:1px solid #555;border-radius:4px;'
            'vertical-align:middle;" title="{}"></span> {}',
            obj.color, obj.color, obj.color,
        )

    @admin.display(description="Hukmdor rasmi")
    def ruler_preview(self, obj):
        return _img_preview(obj.ruler_image, 120)

    @admin.display(description="Qal'a rasmi")
    def castle_preview(self, obj):
        return _img_preview(obj.castle_image, 120)

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"{n} fraksiya faollashtirildi.", messages.SUCCESS)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f"{n} fraksiya faolsizlantirildi.", messages.WARNING)


# ─── Character ──────────────────────────────────────────────────────────────

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = (
        'icon_name', 'title', 'race', 'is_featured',
        'is_active', 'order', 'image_preview',
    )
    list_filter = ('is_featured', 'is_active', 'race')
    search_fields = ('name', 'title', 'description', 'race')
    list_editable = ('order', 'is_featured', 'is_active')
    readonly_fields = ('image_preview',)
    actions = ['feature', 'unfeature', 'activate', 'deactivate']

    fieldsets = (
        (None, {
            'fields': (
                'name', 'title', 'icon', 'race', 'description',
                'image', 'image_preview', 'is_featured', 'is_active', 'order',
            ),
        }),
    )

    @admin.display(description="Qahramon")
    def icon_name(self, obj):
        return f"{obj.icon} {obj.name}"

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        return _img_preview(obj.image, 80)

    @admin.action(description="Bosh sahifaga chiqarish")
    def feature(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, "Tanlanganlar bosh sahifaga chiqarildi.", messages.SUCCESS)

    @admin.action(description="Bosh sahifadan olib tashlash")
    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, "Bosh sahifadan olib tashlandi.", messages.SUCCESS)

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


# ─── Book ───────────────────────────────────────────────────────────────────

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'part_number', 'title', 'has_pdf', 'has_cover',
        'is_active', 'order',
    )
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    list_editable = ('order', 'is_active')
    readonly_fields = ('cover_preview', 'pdf_link')
    actions = ['activate', 'deactivate']

    fieldsets = (
        (None, {
            'fields': (
                'title', 'subtitle', 'part_number', 'order', 'is_active',
                'pdf_file', 'pdf_link', 'cover_image', 'cover_preview',
            ),
        }),
    )

    @admin.display(description="PDF", boolean=True)
    def has_pdf(self, obj):
        return bool(obj.pdf_file)

    @admin.display(description="Muqova", boolean=True)
    def has_cover(self, obj):
        return bool(obj.cover_image)

    @admin.display(description="Muqova ko'rinishi")
    def cover_preview(self, obj):
        return _img_preview(obj.cover_image, 120)

    @admin.display(description="PDF havola")
    def pdf_link(self, obj):
        if obj.pdf_file:
            try:
                return format_html(
                    '<a href="{}" target="_blank">Yuklab olish</a>',
                    obj.pdf_file.url,
                )
            except Exception:
                return "—"
        return "—"

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


# ─── Map Location ───────────────────────────────────────────────────────────

@admin.register(MapLocation)
class MapLocationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'region', 'location_type',
        'pos_x', 'pos_y', 'is_active', 'order', 'image_preview',
    )
    list_filter = ('location_type', 'is_active', 'region')
    search_fields = ('name', 'slug', 'region', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('pos_x', 'pos_y', 'order', 'is_active')
    readonly_fields = ('image_preview',)
    actions = ['activate', 'deactivate']

    fieldsets = (
        ('Asosiy', {
            'fields': (
                'slug', 'name', 'region', 'location_type',
                'description', 'population', 'landmarks',
            ),
        }),
        ('Xarita pozitsiyasi', {
            'fields': ('pos_x', 'pos_y'),
            'description': "Xarita ustidagi foiz koordinatalari (0–100).",
        }),
        ('Rasm va holat', {
            'fields': ('image', 'image_preview', 'is_active', 'order'),
        }),
    )

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        return _img_preview(obj.image, 80)

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


# ─── Site settings (singleton) ──────────────────────────────────────────────

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = (
        'site_title', 'chat_enabled', 'gandalf_enabled',
        'registration_enabled', 'maintenance_mode', 'updated_at',
    )
    readonly_fields = ('updated_at',)

    fieldsets = (
        ('Umumiy', {
            'fields': ('site_title', 'site_tagline', 'hero_text', 'footer_text'),
        }),
        ('Funksiyalar', {
            'fields': (
                'chat_enabled', 'gandalf_enabled',
                'registration_enabled', 'game_download_enabled',
                'max_chat_message_length',
            ),
        }),
        ('Texnik ishlar', {
            'fields': ('maintenance_mode', 'maintenance_message'),
        }),
        ('Meta', {
            'fields': ('updated_at',),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Banned words ───────────────────────────────────────────────────────────

@admin.register(BannedWord)
class BannedWordAdmin(admin.ModelAdmin):
    list_display = ('word', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('word',)
    list_editable = ('is_active',)
    actions = ['activate', 'deactivate']

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


# ─── Announcements ──────────────────────────────────────────────────────────

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'starts_at', 'ends_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'body')
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'
    actions = ['activate', 'deactivate']

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


# ─── User admin qayta ro'yxat ───────────────────────────────────────────────

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)

# ─── Forum ──────────────────────────────────────────────────────────────────

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('icon_name', 'slug', 'order', 'is_active', 'topic_count_display', 'created_at')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('is_active',)
    actions = ['activate', 'deactivate']

    @admin.display(description="Bo'lim")
    def icon_name(self, obj):
        return f"{obj.icon} {obj.name}"

    @admin.display(description="Mavzular")
    def topic_count_display(self, obj):
        return obj.topic_count()

    @admin.action(description="Faollashtirish")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Faolsizlantirish")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        'title_short', 'category', 'author', 'is_pinned', 'is_locked',
        'is_hidden', 'views', 'reply_count_display', 'created_at',
    )
    list_filter = ('category', 'is_pinned', 'is_locked', 'is_hidden', 'created_at')
    search_fields = ('title', 'body', 'author__username')
    list_editable = ('is_pinned', 'is_locked', 'is_hidden')
    date_hierarchy = 'created_at'
    raw_id_fields = ('author',)
    list_per_page = 40
    actions = [
        'pin_topics', 'unpin_topics', 'lock_topics', 'unlock_topics',
        'hide_topics', 'show_topics',
    ]

    fieldsets = (
        (None, {'fields': ('category', 'author', 'title', 'body')}),
        ('Holat', {'fields': ('is_pinned', 'is_locked', 'is_hidden', 'views')}),
        ('Vaqt', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at', 'views')

    @admin.display(description="Sarlavha")
    def title_short(self, obj):
        t = obj.title[:60] + ('…' if len(obj.title) > 60 else '')
        return t

    @admin.display(description="Javoblar")
    def reply_count_display(self, obj):
        return obj.reply_count()

    @admin.action(description="Qadash")
    def pin_topics(self, request, queryset):
        n = queryset.update(is_pinned=True)
        self.message_user(request, f"{n} mavzu qadaldi.", messages.SUCCESS)

    @admin.action(description="Qadashni olib tashlash")
    def unpin_topics(self, request, queryset):
        n = queryset.update(is_pinned=False)
        self.message_user(request, f"{n} mavzudan qadash olib tashlandi.", messages.SUCCESS)

    @admin.action(description="Yopish")
    def lock_topics(self, request, queryset):
        n = queryset.update(is_locked=True)
        self.message_user(request, f"{n} mavzu yopildi.", messages.WARNING)

    @admin.action(description="Ochish")
    def unlock_topics(self, request, queryset):
        n = queryset.update(is_locked=False)
        self.message_user(request, f"{n} mavzu ochildi.", messages.SUCCESS)

    @admin.action(description="Yashirish")
    def hide_topics(self, request, queryset):
        n = queryset.update(is_hidden=True)
        self.message_user(request, f"{n} mavzu yashirildi.", messages.WARNING)

    @admin.action(description="Ko'rsatish")
    def show_topics(self, request, queryset):
        n = queryset.update(is_hidden=False)
        self.message_user(request, f"{n} mavzu ko'rsatildi.", messages.SUCCESS)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('body_preview', 'topic', 'author', 'is_hidden', 'created_at')
    list_filter = ('is_hidden', 'created_at', 'topic__category')
    search_fields = ('body', 'author__username', 'topic__title')
    list_editable = ('is_hidden',)
    date_hierarchy = 'created_at'
    raw_id_fields = ('author', 'topic')
    list_per_page = 50
    actions = ['hide_posts', 'show_posts']

    @admin.display(description="Matn")
    def body_preview(self, obj):
        return (obj.body[:80] + '…') if len(obj.body) > 80 else obj.body

    @admin.action(description="Yashirish")
    def hide_posts(self, request, queryset):
        n = queryset.update(is_hidden=True)
        self.message_user(request, f"{n} javob yashirildi.", messages.WARNING)

    @admin.action(description="Ko'rsatish")
    def show_posts(self, request, queryset):
        n = queryset.update(is_hidden=False)
        self.message_user(request, f"{n} javob ko'rsatildi.", messages.SUCCESS)


# Admin panel sarlavhalari
admin.site.site_header = "⚔ Uzuklar Hukmdori — Boshqaruv paneli"
admin.site.site_title = "Uzuklar Hukmdori Admin"
admin.site.index_title = "Hamjamiyat va saytni to'liq boshqarish"
