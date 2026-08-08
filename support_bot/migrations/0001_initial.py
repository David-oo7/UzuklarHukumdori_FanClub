import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TelegramUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("telegram_id", models.BigIntegerField(db_index=True, unique=True)),
                ("username", models.CharField(blank=True, max_length=255, null=True)),
                ("first_name", models.CharField(blank=True, max_length=255, null=True)),
                ("last_name", models.CharField(blank=True, max_length=255, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Telegram foydalanuvchi",
                "verbose_name_plural": "Telegram foydalanuvchilar",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Ochiq"),
                            ("in_progress", "Jarayonda"),
                            ("closed", "Yopilgan"),
                        ],
                        db_index=True,
                        default="open",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "telegram_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tickets",
                        to="support_bot.telegramuser",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ticket",
                "verbose_name_plural": "Ticketlar",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "sender_type",
                    models.CharField(
                        choices=[("user", "Foydalanuvchi"), ("admin", "Admin")],
                        max_length=10,
                    ),
                ),
                ("sender_telegram_id", models.BigIntegerField()),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ticket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="support_bot.ticket",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ticket xabari",
                "verbose_name_plural": "Ticket xabarlari",
                "ordering": ["created_at"],
            },
        ),
    ]
