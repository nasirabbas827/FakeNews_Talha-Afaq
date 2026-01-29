from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import (
    CustomUserChangeForm, ProfileForm, CustomUserCreationForm,
    CustomAuthenticationForm, NewsArticleForm
)
from .models import Profile, ActivityLog, NewsArticle, AnalysisResult
import joblib
import numpy as np
import re
import html
import string

# Load your trained model and vectorizer
MODEL_PATH = 'models/fake_news_model_20260129_124205.joblib'
VECTORIZER_PATH = 'models/tfidf_vectorizer_20260129_124205.joblib'

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

# =====================================================
# Text Preprocessing Function
# =====================================================
def preprocess_text(text):
    """
    Comprehensive preprocessing for news/article text:
    - Lowercasing
    - Remove URLs, mentions, hashtags
    - Decode HTML entities
    - Remove numbers and punctuation
    - Remove non-ASCII characters
    - Expand common contractions
    - Remove extra whitespace and newlines
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Remove mentions, hashtags
    text = re.sub(r'@\w+|#\w+', '', text)
    
    # Expand contractions (basic)
    contractions = {
        "won't": "will not",
        "wouldn't": "would not",
        "can't": "cannot",
        "n't": " not",
        "'re": " are",
        "'s": " is",
        "'d": " would",
        "'ll": " will",
        "'t": " not",
        "'ve": " have",
        "'m": " am"
    }
    for k, v in contractions.items():
        text = re.sub(k, v, text)
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7f]',r'', text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# =====================================================
# Auth & Profile Views
# =====================================================
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, "Invalid credentials.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('user_login')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            ActivityLog.objects.create(user=request.user, action="Changed password")
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


@login_required
def home(request):
    recent_news = NewsArticle.objects.order_by('-submitted_at')[:5]
    context = {
        'recent_news': recent_news
    }
    return render(request, 'dashboard.html', context)


@login_required
def user_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    user_form = CustomUserChangeForm(instance=request.user)
    profile_form = ProfileForm(instance=profile)

    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            ActivityLog.objects.create(user=request.user, action="Updated profile")
            messages.success(request, "Profile updated successfully!")
            return redirect('user_profile')

    return render(request, 'user_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    })


# =====================================================
# Submit News View with Preprocessing & Prediction
# =====================================================
@login_required
def submit_news(request):
    if request.method == 'POST':
        form = NewsArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.user = request.user
            article.save()

            # Preprocess content
            processed_text = preprocess_text(article.content)

            # Predict using the trained model
            X = vectorizer.transform([processed_text])
            pred_class = model.predict(X)[0]
            pred_prob = np.max(model.predict_proba(X)) * 100  # confidence

            # Save AnalysisResult
            AnalysisResult.objects.create(
                article=article,
                prediction=pred_class,
                confidence_score=round(pred_prob, 2),
                model_version='v1.0'
            )

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action=f"Submitted news article {article.id} and predicted {pred_class}"
            )

            messages.success(
                request,
                f"News submitted successfully! Prediction: {pred_class} ({round(pred_prob,2)}%)"
            )
            return redirect('dashboard')
    else:
        form = NewsArticleForm()

    return render(request, 'submit_news.html', {'form': form})
