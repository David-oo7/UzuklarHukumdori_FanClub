from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_supportteammember_link_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='winter_theme_mode',
            field=models.CharField(
                choices=[
                    ('auto', "Avtomatik (Dekabr—Fevral oylarida o'zi yoqiladi)"),
                    ('always_on', 'Doim yoqilgan'),
                    ('always_off', "Doim o'chirilgan"),
                ],
                default='auto',
                help_text="Avtomatik rejimda tema Dekabr, Yanvar, Fevral oylarida o'zi yoqiladi.",
                max_length=12,
                verbose_name='Qishgi tema rejimi',
            ),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='winter_snow_effect',
            field=models.BooleanField(
                default=True,
                help_text="Qishgi tema yoqilganda ekranda qor yog'ishi animatsiyasi ko'rsatilsinmi.",
                verbose_name="Qor yog'ish effekti",
            ),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='winter_snow_intensity',
            field=models.CharField(
                choices=[('light', 'Kam'), ('normal', "O'rta"), ('heavy', 'Kuchli')],
                default='normal',
                max_length=10,
                verbose_name='Qor zichligi',
            ),
        ),
    ]
