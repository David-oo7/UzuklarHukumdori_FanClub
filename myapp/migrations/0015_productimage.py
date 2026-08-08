from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0014_shop'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='shop/gallery/', verbose_name='Rasm')),
                ('alt_text', models.CharField(blank=True, max_length=150, verbose_name='Rasm tavsifi')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='gallery_images',
                    to='myapp.product',
                    verbose_name='Mahsulot',
                )),
            ],
            options={
                'verbose_name': 'Mahsulot rasmi',
                'verbose_name_plural': 'Mahsulot rasmlari (galereya)',
                'ordering': ['order', 'id'],
            },
        ),
    ]
