from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, SupportTicket


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        label="Email (ixtiyoriy)",
        widget=forms.EmailInput(attrs={
            'placeholder': 'email@example.com',
            'autocomplete': 'email',
        }),
    )
    username = forms.CharField(
        label="Foydalanuvchi nomi",
        max_length=150,
        help_text="Harflar, raqamlar va @/./+/-/_ belgilariga ruxsat.",
        widget=forms.TextInput(attrs={
            'placeholder': 'username',
            'autocomplete': 'username',
        }),
    )
    password1 = forms.CharField(
        label="Parol",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Parol',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label="Parolni tasdiqlang",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Parolni qayta yozing',
            'autocomplete': 'new-password',
        }),
    )
    favorite_race = forms.ChoiceField(
        choices=[('', 'Xalqingizni tanlang')] + list(UserProfile.RACE_CHOICES),
        required=True,
        label="Irqingiz",
        widget=forms.Select(attrs={'id': 'id_favorite_race'}),
    )
    faction = forms.ChoiceField(
        choices=[('', 'Avval irqni tanlang')],
        required=False,
        label="Fraksiyangiz",
        help_text="Faqat irqingizga mos fraksiyalar ko'rsatiladi.",
        widget=forms.Select(attrs={'id': 'id_faction'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'favorite_race', 'faction']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faction'].choices = [
            ('', 'Fraksiya tanlanmagan')
        ] + list(UserProfile.FACTION_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        race = cleaned_data.get('favorite_race')
        faction = cleaned_data.get('faction')
        allowed_factions = UserProfile.RACE_FACTIONS.get(race, ())

        if faction and faction not in allowed_factions:
            self.add_error('faction', "Bu fraksiya tanlangan irqqa mos emas.")
        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'favorite_race', 'faction']
        labels = {
            'avatar': 'Avatar (rasm)',
            'bio': 'Qisqa tavsif',
            'favorite_race': 'Irq',
            'faction': 'Fraksiya',
        }
        widgets = {
            'bio': forms.TextInput(attrs={
                'maxlength': 200,
                'placeholder': "O'zingiz haqingizda qisqacha...",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        race = cleaned_data.get('favorite_race')
        faction = cleaned_data.get('faction')
        if faction and faction not in UserProfile.RACE_FACTIONS.get(race, ()):
            self.add_error('faction', "Bu fraksiya tanlangan irqqa mos emas.")
        return cleaned_data


class TopicCreateForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label="Sarlavha",
        widget=forms.TextInput(attrs={
            'placeholder': "Mavzu sarlavhasi...",
            'class': 'form-input',
        }),
    )
    body = forms.CharField(
        max_length=5000,
        label="Matn",
        widget=forms.Textarea(attrs={
            'rows': 8,
            'placeholder': "O'ylaringizni yozing...",
            'class': 'form-input',
        }),
    )


class PostCreateForm(forms.Form):
    body = forms.CharField(
        max_length=5000,
        label="Javob",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': "Javobingizni yozing...",
            'class': 'form-input',
        }),
    )


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'category', 'description', 'priority', 'attachment']
        labels = {
            'subject': 'Subject',
            'category': 'Category',
            'description': 'Description',
            'priority': 'Priority',
            'attachment': 'Screenshot / fayl',
        }
        widgets = {
            'subject': forms.TextInput(attrs={
                'placeholder': 'Qisqa sarlavha...',
                'class': 'form-input',
                'maxlength': 200,
            }),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={
                'rows': 7,
                'placeholder': 'Muammo yoki taklifni batafsil yozing...',
                'class': 'form-input',
            }),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }

    def clean_attachment(self):
        f = self.cleaned_data.get('attachment')
        if not f:
            return f
        max_size = 8 * 1024 * 1024  # 8 MB
        if f.size > max_size:
            raise forms.ValidationError("Fayl hajmi 8 MB dan oshmasligi kerak.")
        allowed = {
            'image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif',
            'application/pdf', 'application/zip', 'application/x-zip-compressed',
            'text/plain', 'application/octet-stream',
        }
        name = (f.name or '').lower()
        ok_ext = name.endswith((
            '.png', '.jpg', '.jpeg', '.webp', '.gif',
            '.pdf', '.zip', '.txt', '.log',
        ))
        ctype = getattr(f, 'content_type', '') or ''
        if not ok_ext and ctype not in allowed:
            raise forms.ValidationError(
                "Ruxsat etilgan formatlar: PNG, JPG, JPEG, WEBP, GIF, PDF, ZIP, TXT, LOG."
            )
        return f
