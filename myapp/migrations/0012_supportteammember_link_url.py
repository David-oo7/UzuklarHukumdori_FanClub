from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_support_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportteammember',
            name='link_url',
            field=models.URLField(blank=True, help_text='Kartaga bosilganda ochiladigan sahifa (Telegram, GitHub, profil va h.k.).', max_length=500, verbose_name='Havola (URL)'),
        ),
    ]
