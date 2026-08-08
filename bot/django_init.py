"""
Botni mustaqil (Django dev-server'siz) process sifatida ishga tushirganda
ham Django ORM'dan (support_bot ilovasi modellaridan) foydalanish uchun
Django'ni qo'lda sozlab beradi.

Bu modul bot ishga tushishi bilan BIRINCHI bo'lib import qilinishi shart —
boshqa har qanday `support_bot.models` importidan oldin.
"""

import os
import sys

import django

from bot import config

# manage.py bilan bir xil papkada joylashgan Django loyihasi ildizini
# Python yo'liga (PYTHONPATH) qo'shamiz. Agar support_bot va bot papkalari
# Django loyihangiz ildizida (manage.py bilan bir joyda) tursa, bu qadam
# shart emas, lekin xavfsizlik uchun qoldirilgan.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", config.DJANGO_SETTINGS_MODULE)

django.setup()
