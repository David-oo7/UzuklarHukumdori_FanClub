from django.db import migrations


def seed_categories(apps, schema_editor):
    ForumCategory = apps.get_model('myapp', 'ForumCategory')
    defaults = [
        {
            'name': 'Umumiy suhbat',
            'slug': 'umumiy',
            'description': 'O‘rta Yer va sayt haqida erkin suhbat',
            'icon': '📜',
            'order': 1,
        },
        {
            'name': 'Kitoblar va film',
            'slug': 'kitoblar',
            'description': 'Tolkien asarlari, tarjimalar va filmlar',
            'icon': '📖',
            'order': 2,
        },
        {
            'name': 'Fraksiyalar',
            'slug': 'fraksiyalar',
            'description': 'Gondor, Rohan, Mordor va boshqa xalqlar',
            'icon': '⚔',
            'order': 3,
        },
        {
            'name': 'Savol-javob',
            'slug': 'savol-javob',
            'description': 'Bilmaganlaringizni so‘rang — jamoa javob beradi',
            'icon': '❓',
            'order': 4,
        },
        {
            'name': 'Ijod va fan-art',
            'slug': 'ijod',
            'description': 'Hikoyalar, she’rlar, rasmlar va fan-nazariyalar',
            'icon': '✨',
            'order': 5,
        },
    ]
    for d in defaults:
        ForumCategory.objects.get_or_create(slug=d['slug'], defaults=d)


def unseed(apps, schema_editor):
    ForumCategory = apps.get_model('myapp', 'ForumCategory')
    ForumCategory.objects.filter(
        slug__in=['umumiy', 'kitoblar', 'fraksiyalar', 'savol-javob', 'ijod']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_community_forum'),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed),
    ]
