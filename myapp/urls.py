from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # User Authentication
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login_view, name='user_login'),
    path('logout/', views.logout_view, name='logout'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('analysis/history/', views.analysis_history, name='analysis_history'),
    path('datasets/', views.dataset_list, name='dataset_list'),

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Dashboard
    path('', views.home, name='dashboard'),
    path('dashboard/', views.home, name='dashboard'),

    # User Profile & Password Change
    path('profile/', views.user_profile, name='user_profile'),
    path('change_password/', views.change_password, name='change_password'),

    # News Submission & Analysis
    path('submit_news/', views.submit_news, name='submit_news'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
