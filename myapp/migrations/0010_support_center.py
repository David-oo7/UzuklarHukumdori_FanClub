# Generated manually for Support Center

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0009_advertisement_banner_style_advertisement_side_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_number', models.PositiveIntegerField(editable=False, unique=True, verbose_name='Ticket №')),
                ('subject', models.CharField(max_length=200, verbose_name='Mavzu')),
                ('category', models.CharField(choices=[('bug', '🐛 Bug Report'), ('suggestion', '💡 Suggestion'), ('report_user', '⚠ Report User'), ('account', '🔒 Account Problem'), ('other', '❓ Other')], default='other', max_length=20, verbose_name='Kategoriya')),
                ('description', models.TextField(max_length=5000, verbose_name='Tavsif')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10, verbose_name='Muhimlik')),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('closed', 'Closed')], default='open', max_length=20, verbose_name='Holat')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='support/tickets/', verbose_name='Ilova (screenshot / fayl)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan')),
                ('closed_at', models.DateTimeField(blank=True, null=True, verbose_name='Yopilgan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_tickets', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Support ticket',
                'verbose_name_plural': 'Support ticketlar',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='TicketMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(blank=True, max_length=3000, verbose_name='Xabar')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='support/messages/', verbose_name='Fayl')),
                ('is_staff_reply', models.BooleanField(default=False, verbose_name='Admin javobi')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ticket_messages', to=settings.AUTH_USER_MODEL, verbose_name='Muallif')),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='myapp.supportticket', verbose_name='Ticket')),
            ],
            options={
                'verbose_name': 'Ticket xabari',
                'verbose_name_plural': 'Ticket xabarlari',
                'ordering': ['created_at'],
            },
        ),
    ]
