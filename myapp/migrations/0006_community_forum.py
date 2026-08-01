# Generated manually for community forum

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0005_userprofile_faction'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_seen',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Oxirgi faollik'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='reputation',
            field=models.IntegerField(default=0, verbose_name="Obro'"),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_moderator',
            field=models.BooleanField(default=False, verbose_name='Moderator'),
        ),
        migrations.CreateModel(
            name='ForumCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nomi')),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Tavsif')),
                ('icon', models.CharField(default='📜', max_length=10, verbose_name='Ikonka')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "Forum bo'limi",
                'verbose_name_plural': "Forum bo'limlari",
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Sarlavha')),
                ('body', models.TextField(max_length=5000, verbose_name='Matn')),
                ('is_pinned', models.BooleanField(default=False, verbose_name='Qadalgan')),
                ('is_locked', models.BooleanField(default=False, verbose_name='Yopilgan')),
                ('is_hidden', models.BooleanField(default=False, verbose_name='Yashirilgan')),
                ('views', models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='topics', to=settings.AUTH_USER_MODEL, verbose_name='Muallif')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='myapp.forumcategory', verbose_name="Bo'lim")),
            ],
            options={
                'verbose_name': 'Mavzu',
                'verbose_name_plural': 'Mavzular',
                'ordering': ['-is_pinned', '-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(max_length=5000, verbose_name='Matn')),
                ('is_hidden', models.BooleanField(default=False, verbose_name='Yashirilgan')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forum_posts', to=settings.AUTH_USER_MODEL, verbose_name='Muallif')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='myapp.topic', verbose_name='Mavzu')),
            ],
            options={
                'verbose_name': 'Javob',
                'verbose_name_plural': 'Javoblar',
                'ordering': ['created_at'],
            },
        ),
    ]
