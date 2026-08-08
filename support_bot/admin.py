from django.contrib import admin

from .models import TelegramUser, Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ("sender_type", "sender_telegram_id", "message", "created_at")
    can_delete = False


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "last_name", "created_at")
    search_fields = ("telegram_id", "username", "first_name", "last_name")
    ordering = ("-created_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_user", "status", "created_at", "updated_at", "closed_at")
    list_filter = ("status",)
    search_fields = ("id", "telegram_user__username", "telegram_user__telegram_id", "message")
    ordering = ("-created_at",)
    inlines = [TicketMessageInline]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "sender_type", "sender_telegram_id", "created_at")
    list_filter = ("sender_type",)
    search_fields = ("message", "sender_telegram_id")
    ordering = ("-created_at",)
