from django.db import models


class TelegramUser(models.Model):
    """Telegram orqali botga murojaat qilgan foydalanuvchi."""

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Telegram foydalanuvchi"
        verbose_name_plural = "Telegram foydalanuvchilar"
        ordering = ["-created_at"]

    def __str__(self):
        if self.username:
            return f"@{self.username} ({self.telegram_id})"
        full_name = " ".join(filter(None, [self.first_name, self.last_name]))
        return full_name or str(self.telegram_id)


class Ticket(models.Model):
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Ochiq"),
        (STATUS_IN_PROGRESS, "Jarayonda"),
        (STATUS_CLOSED, "Yopilgan"),
    ]

    STATUS_EMOJI = {
        STATUS_OPEN: "🟡 Ochiq",
        STATUS_IN_PROGRESS: "🔵 Jarayonda",
        STATUS_CLOSED: "🟢 Yopilgan",
    }

    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="tickets"
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Ticketlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.id} — {self.telegram_user} [{self.status}]"

    def status_display_uz(self):
        return self.STATUS_EMOJI.get(self.status, self.status)


class TicketMessage(models.Model):
    SENDER_USER = "user"
    SENDER_ADMIN = "admin"

    SENDER_CHOICES = [
        (SENDER_USER, "Foydalanuvchi"),
        (SENDER_ADMIN, "Admin"),
    ]

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages"
    )
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender_telegram_id = models.BigIntegerField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket xabari"
        verbose_name_plural = "Ticket xabarlari"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender_type}] Ticket #{self.ticket_id}: {self.message[:40]}"
