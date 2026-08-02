"""
URL configuration for myproject2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('muhokama/', views.muhokama_page, name='muhokama_page'),
    path('gandalf/', views.gandalf_page, name='gandalf_page'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home', http_method_names=['get', 'post']), name='logout'),
    path('chat/upload-image/', views.chat_upload_image, name='chat_upload_image'),
    path('gandalf/ask/', views.ask_gandalf, name='ask_gandalf'),
    path('profile/', views.profile, name='profile'),
    path('faction/<slug:slug>/', views.faction_detail, name='faction_detail'),
    path('faction/<slug:slug>/castle/', views.faction_castle, name='faction_castle'),
    path('xarita/', views.xarita_page, name='xarita_page'),
    # Hamjamiyat / Forum
    path('hamjamiyat/', views.hamjamiyat_page, name='hamjamiyat'),
    path('forum/', views.forum_index, name='forum_index'),
    path('forum/<slug:slug>/', views.forum_category, name='forum_category'),
    path('forum/<slug:slug>/yangi/', views.topic_create, name='topic_create'),
    path('forum/mavzu/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('a/<str:username>/', views.member_profile, name='member_profile'),
]

# Password reset (Django built-in views)
urlpatterns += [
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]

# Media (PDF, avatar, chat rasmlari) — lokal va Render uchun
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
