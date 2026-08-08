from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0010_support_center'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('developer', '🛠 Developer'), ('admin', '⚔ Site Admin'), ('support', '📜 Support')], default='support', max_length=20, verbose_name='Lavozim')),
                ('title', models.CharField(blank=True, help_text='Masalan: Bosh dasturchi, Moderator, Support agent', max_length=120, verbose_name='Unvon')),
                ('bio', models.CharField(blank=True, max_length=300, verbose_name='Qisqa bio')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('show_on_page', models.BooleanField(default=True, verbose_name="Jamoa sahifasida ko'rsatish")),
                ('can_manage_tickets', models.BooleanField(default=True, help_text="Yoqilsa, ushbu a'zo support ticketlarga javob bera oladi (staff bo'lmasa ham).", verbose_name='Ticketlarni boshqara oladi')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='support_team', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': "Support jamoa a'zosi",
                'verbose_name_plural': 'Support jamoa',
                'ordering': ['order', 'role', 'user__username'],
            },
        ),
    ]
