from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('myapp', '0004_site_management')]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='favorite_race',
            field=models.CharField(
                blank=True,
                choices=[
                    ('elf', 'Elflar'), ('human', 'Odamlar'),
                    ('dwarf', 'Gnomlar'), ('hobbit', 'Xobbitlar'),
                    ('ent', 'Entlar'), ('ainur', 'Aynurlar'),
                    ('orc', 'Orklar'), ('uruk_hai', 'Uruk-xaylar'),
                    ('troll', 'Trollar'), ('dragon', 'Ajdaholar'),
                    ('warg', 'Varglar'),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='faction',
            field=models.CharField(
                blank=True,
                choices=[
                    ('gondor', 'Gondor'), ('rohan', 'Rohan'),
                    ('rivendell', 'Rivendell'), ('lothlorien', 'Lothlorien'),
                    ('woodland_realm', 'Woodland Realm'), ('erebor', 'Erebor'),
                    ('mordor', 'Mordor'), ('isengard', 'Isengard'),
                    ('goblin', 'Goblinlar'),
                ],
                max_length=30,
            ),
        ),
    ]
