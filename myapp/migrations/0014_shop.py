from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0013_sitesetting_winter_theme'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Kategoriya nomi')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('icon', models.CharField(default='💍', max_length=10, verbose_name='Emoji')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
            ],
            options={
                'verbose_name': "Do'kon kategoriyasi",
                'verbose_name_plural': "Do'kon kategoriyalari",
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Mahsulot nomi')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Tavsif')),
                ('price', models.DecimalField(decimal_places=0, max_digits=12, verbose_name="Narx (so'm)")),
                ('old_price', models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True, verbose_name='Eski narx (chegirma)')),
                ('image', models.ImageField(blank=True, null=True, upload_to='shop/', verbose_name='Asosiy rasm')),
                ('stock', models.PositiveIntegerField(default=10, verbose_name='Ombordagi soni')),
                ('is_active', models.BooleanField(default=True, verbose_name='Sotuvda')),
                ('is_featured', models.BooleanField(default=False, verbose_name='Tanlangan (bosh sahifa)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='myapp.shopcategory', verbose_name='Kategoriya')),
            ],
            options={
                'verbose_name': 'Mahsulot',
                'verbose_name_plural': 'Mahsulotlar',
                'ordering': ['order', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='Ism familiya')),
                ('phone', models.CharField(max_length=30, verbose_name='Telefon')),
                ('address', models.TextField(verbose_name='Manzil')),
                ('note', models.TextField(blank=True, verbose_name='Izoh')),
                ('status', models.CharField(choices=[('new', 'Yangi'), ('confirmed', 'Tasdiqlangan'), ('shipped', 'Yuborilgan'), ('done', 'Yakunlangan'), ('cancelled', 'Bekor qilingan')], default='new', max_length=20, verbose_name='Holat')),
                ('total', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Jami summa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop_orders', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Buyurtma',
                'verbose_name_plural': 'Buyurtmalar',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200, verbose_name='Mahsulot nomi (saqlangan)')),
                ('price', models.DecimalField(decimal_places=0, max_digits=12, verbose_name='Narx')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Soni')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='myapp.order', verbose_name='Buyurtma')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items', to='myapp.product', verbose_name='Mahsulot')),
            ],
            options={
                'verbose_name': 'Buyurtma elementi',
                'verbose_name_plural': 'Buyurtma elementlari',
            },
        ),
    ]
