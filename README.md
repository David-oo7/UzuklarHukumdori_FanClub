# Telegram Support Bot — Django integratsiyasi

Bu paket mavjud Django loyihangizga **buzmasdan** qo'shiladigan support-ticket
tizimi: bir tomondan Django ilovasi (`support_bot`), ikkinchi tomondan
mustaqil ishlaydigan Telegram bot (`bot/`, aiogram 3.x asosida), ikkalasi ham
bitta PostgreSQL bazasidan foydalanadi.

## 1. Loyihaga qanday joylashtiriladi

Arxivni oching va ichidagi ikkita papkani (`support_bot/` va `bot/`) hamda
`requirements.txt`, `.env.example`, `.gitignore` fayllarini **Django
loyihangiz ildiziga** (ya'ni `manage.py` bilan bir xil papkaga) ko'chiring:

```
sizning-loyihangiz/
├── manage.py
├── myproject2/              ← mavjud Django settings papkangiz
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── support_bot/             ← YANGI: ushbu arxivdan
├── bot/                     ← YANGI: ushbu arxivdan
├── logs/                    ← YANGI
├── .env                     ← YANGI (to'ldirishingiz kerak)
├── .env.example             ← YANGI
├── .gitignore                ← mavjud bo'lsa, ichiga birlashtiring
└── requirements.txt          ← mavjud bo'lsa, ichiga birlashtiring
```

**Muhim:** agar loyihangizda `myproject2` boshqacha nomlangan bo'lsa
(masalan `config`, `core` va h.k.), quyidagi ikki joyda shu nomga moslang:
- `.env` faylidagi `DJANGO_SETTINGS_MODULE`
- Pastdagi 2-qadamdagi `settings.py` ga qo'shiladigan `INSTALLED_APPS`

## 2. Django settings.py ga app qo'shish

Mavjud `settings.py` faylingizni o'chirmang — faqat quyidagi bitta qatorni
`INSTALLED_APPS` ro'yxatiga qo'shing:

```python
INSTALLED_APPS = [
    # ... mavjud ilovalaringiz ...
    "support_bot",
]
```

Boshqa hech narsani o'zgartirish shart emas — `support_bot` o'z modellari
(`TelegramUser`, `Ticket`, `TicketMessage`) va admin panelga ro'yxatdan
o'tishi bilan birga to'liq mustaqil ilova.

## 3. Kerakli kutubxonalarni o'rnatish

Loyiha papkasida (cmd orqali):

```
pip install -r requirements.txt
```

Agar loyihangizda allaqachon `requirements.txt` bo'lsa, ikkala faylni
birlashtiring (dublikat paketlarni olib tashlang).

## 4. PostgreSQL sozlash

1. PostgreSQL da yangi baza yarating (agar mavjud Django loyihangiz allaqachon
   PostgreSQL ishlatayotgan bo'lsa, xuddi shu bazadan foydalansangiz ham bo'ladi —
   `support_bot` o'z jadvallarini shu bazaga qo'shadi):

   ```sql
   CREATE DATABASE support_bot_db;
   ```

2. Django'ning `settings.py` faylidagi `DATABASES` sozlamasi PostgreSQL'ga
   ulanganiga ishonch hosil qiling. Agar hali sqlite ishlatayotgan bo'lsangiz,
   masalan:

   ```python
   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.postgresql",
           "NAME": "support_bot_db",
           "USER": "postgres",
           "PASSWORD": "sizning_parolingiz",
           "HOST": "localhost",
           "PORT": "5432",
       }
   }
   ```

3. Migratsiyalarni yarating va qo'llang:

   ```
   python manage.py makemigrations support_bot
   python manage.py migrate
   ```

   (Arxivda tayyor `0001_initial.py` migratsiya fayli ham bor —
   `makemigrations` uni allaqachon to'g'ri deb topsa, qayta yaratmaydi.)

## 5. `.env` faylini to'ldirish

`.env` faylini oching va quyidagilarni kiriting:

```
BOT_TOKEN=123456:ABC-DEF...          ← @BotFather dan olinadi
ADMIN_IDS=123456789,987654321        ← admin bo'ladigan Telegram ID'lar
DATABASE_URL=postgres://postgres:parol@localhost:5432/support_bot_db
DJANGO_SETTINGS_MODULE=myproject2.settings   ← o'zingizning nomingizga moslang
MY_TICKETS_LIMIT=5
LOG_DIR=logs
```

Telegram ID'ingizni bilish uchun Telegram'da **@userinfobot** ga `/start`
yozing — u sizga ID'ingizni yuboradi.

`.env` fayli `.gitignore` orqali GitHub'ga push qilinmaydi — faqat
`.env.example` push qilinadi.

## 6. Telegram botni ishga tushirish

Bot Django dev-serveridan **mustaqil, alohida process** sifatida ishlaydi
(lekin bitta bazadan foydalanadi). Loyiha ildizida:

```
python -m bot.run
```

Konsolda quyidagiga o'xshash xabarni ko'rasiz:

```
Support bot ishga tushmoqda...
Bot polling rejimida ishga tushdi. Adminlar: {123456789, 987654321}
```

Botni Django serveringiz bilan bir vaqtda ishlatish uchun ikkita alohida
terminal oyna kerak bo'ladi: birida `python manage.py runserver` (yoki
Daphne), ikkinchisida `python -m bot.run`.

Server(Render/o'z laptopingiz)da doimiy ishlashi uchun botni `systemd`
xizmati, `pm2`, yoki Windows'da `nssm` kabi vosita orqali background
process sifatida ishga tushirishingiz tavsiya etiladi.

## 7. Django bilan qanday integratsiya qilingan

- `support_bot/` — oddiy Django ilovasi: `TelegramUser`, `Ticket`,
  `TicketMessage` modellari, va ularning barchasi Django admin panelida
  (`/admin/`) ko'rinadi va tahrirlanadi.
- `bot/` — aiogram 3.x asosidagi mustaqil process. `bot/django_init.py`
  fayli ishga tushishi bilan `django.setup()` ni chaqiradi, shundan keyin
  bot ichidagi barcha service'lar (`bot/services/ticket_service.py`)
  to'g'ridan-to'g'ri **Django ORM** orqali (`Ticket.objects...` va h.k.)
  bazaga yozadi/o'qiydi.
- ORM chaqiruvlari `asgiref.sync_to_async` bilan o'ralgan, chunki aiogram
  asinxron, Django ORM esa sinxron ishlaydi.
- Django loyihangizning mavjud `urls.py`, `views.py`, boshqa ilovalari
  **umuman tegilmagan** — faqat bitta yangi ilova (`support_bot`) va
  `INSTALLED_APPS` ga bitta qator qo'shiladi.
- Xohlasangiz, kelajakda saytingizning o'zida (Django view orqali) ham
  foydalanuvchi ticketlarini ko'rsatish mumkin bo'ladi — chunki ma'lumotlar
  oddiy Django modeli sifatida saqlanadi.

## Botning ishlash tartibi

1. Foydalanuvchi `/start` bosadi → asosiy menyu chiqadi.
2. **📝 Murojaat yuborish** → matn yozadi → PostgreSQL'ga `Ticket` sifatida
   saqlanadi va barcha adminlarga xabar yuboriladi (💬 Javob berish /
   ✅ Ticketni yopish tugmalari bilan).
3. Admin **💬 Javob berish** bossa → javobini yozadi → foydalanuvchiga
   yetkaziladi va `TicketMessage` sifatida saqlanadi.
4. Foydalanuvchi ochiq ticketi bo'lsa, keyingi oddiy xabarlari ham
   avtomatik o'sha ticketga qo'shilib, adminlarga yuboriladi.
5. Admin **✅ Ticketni yopish** bossa → status `closed` bo'ladi,
   foydalanuvchiga xabar boradi.
6. **📋 Mening murojaatlarim** → foydalanuvchining oxirgi (`MY_TICKETS_LIMIT`
   ta) ticketlari status bilan ko'rsatiladi.

## Xatoliklardan himoya

- Foydalanuvchi botni bloklagan bo'lsa — bot yiqilmaydi, log fayliga
  yoziladi (`logs/bot.log`), admin/foydalanuvchiga xabar yuborilmaydi xolos.
- Noto'g'ri/mavjud bo'lmagan ticket ID bilan amal bajarilsa — foydalanuvchiga
  aniq xabar ko'rsatiladi.
- Yopilgan ticketga javob yuborishga urinish bloklanadi.
- Admin bo'lmagan foydalanuvchi admin tugmalarini (Javob berish / Yopish)
  bossa — "ruxsat yo'q" degan xabar ko'rsatiladi, hech qanday amal
  bajarilmaydi.
- Barcha kutilmagan xatolar `logs/bot.log` fayliga to'liq stack-trace bilan
  yoziladi, bot ishlashda davom etadi.

## Papka tuzilishi

```
support_bot/            ← Django ilovasi (modellar, admin)
├── models.py
├── admin.py
├── apps.py
└── migrations/

bot/                     ← Telegram bot (aiogram 3.x)
├── run.py                ← ishga tushirish nuqtasi
├── config.py              ← .env o'qish
├── django_init.py         ← Django ORM'ni ishga tushirish
├── loader.py               ← Bot/Dispatcher yaratish
├── logging_setup.py        ← logging konfiguratsiyasi
├── filters.py               ← IsAdmin filter
├── handlers/
│   ├── user_handlers.py
│   └── admin_handlers.py
├── keyboards/
│   ├── reply.py
│   └── inline.py
├── services/
│   ├── ticket_service.py
│   └── notify_service.py
├── states/
│   └── ticket_states.py
└── middlewares/
    └── logging_middleware.py

logs/                    ← bot.log shu yerga yoziladi
.env / .env.example
.gitignore
requirements.txt
```

## Yaratilgan / o'zgartirilgan fayllar xulosasi

**Yaratilgan (yangi) fayllar:** yuqoridagi papka tuzilishidagi barcha
fayllar — `support_bot/` va `bot/` papkalari to'liq yangi, mavjud loyihangizga
hech narsani o'chirmasdan qo'shiladi.

**O'zgartirilishi kerak bo'lgan mavjud fayl:** faqat bitta —
`settings.py` dagi `INSTALLED_APPS` ro'yxatiga `"support_bot"` qatori
qo'shiladi (2-bo'limga qarang). Boshqa hech qanday mavjud faylga tegilmaydi.
