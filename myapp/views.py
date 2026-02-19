from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import (
    CustomUserChangeForm, ProfileForm, CustomUserCreationForm,
    CustomAuthenticationForm, NewsArticleForm
)
from .models import Profile, ActivityLog, NewsArticle, AnalysisResult , ModelTrainingLog
from django.core.paginator import Paginator
from django.db.models import Avg
import joblib
import numpy as np
import re
import html
import string
import io
import base64
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors, pagesizes
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether
from reportlab.platypus import LongTable
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from openpyxl import Workbook

from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404
from .models import Dataset
import os


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
    articles = NewsArticle.objects.filter(user=request.user) \
        .select_related('analysis') \
        .order_by('-submitted_at')

    analyzed = articles.filter(analysis__isnull=False)

    total_count = analyzed.count()
    real_count = analyzed.filter(analysis__prediction='Real').count()
    fake_count = analyzed.filter(analysis__prediction='Fake').count()

    # ---------------------------------------------
    # Get Latest Model Accuracy from Training Log
    # ---------------------------------------------
    latest_training = ModelTrainingLog.objects.order_by('-trained_at').first()

    model_accuracy = 0
    model_precision = 0
    model_recall = 0
    model_f1 = 0

    if latest_training:
        model_accuracy = latest_training.accuracy
        model_precision = latest_training.precision
        model_recall = latest_training.recall
        model_f1 = latest_training.f1_score

    # ---------------------------------------------
    # Generate Pie Chart (Only if data exists)
    # ---------------------------------------------
    graph = None

    if total_count > 0:
        fig, ax = plt.subplots()

        ax.pie(
            [real_count, fake_count],
            labels=['Real', 'Fake'],
            autopct='%1.1f%%'
        )
        ax.set_title("Prediction Distribution")

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)

        image_png = buffer.getvalue()
        graph = base64.b64encode(image_png).decode('utf-8')

        buffer.close()
        plt.close(fig)

    context = {
        'recent_news': articles[:10],
        'total_count': total_count,
        'model_accuracy': model_accuracy,
        'model_precision': model_precision,
        'model_recall': model_recall,
        'model_f1': model_f1,
        'chart': graph
    }

    return render(request, 'dashboard.html', context)

@login_required
def export_excel(request):
    analyzed = AnalysisResult.objects.filter(article__user=request.user)\
        .select_related('article')

    wb = Workbook()
    ws = wb.active
    ws.title = "Classification Results"

    ws.append(["Content", "Prediction", "Confidence", "Date"])

    for item in analyzed:
        ws.append([
            item.article.content,
            item.prediction,
            float(item.confidence_score),
            item.analyzed_at.strftime("%Y-%m-%d")
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=classification_results.xlsx'
    wb.save(response)
    return response



@login_required
def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=classification_results.pdf'

    doc = SimpleDocTemplate(
        response,
        pagesize=pagesizes.A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Classification Report", styles['Title']))
    elements.append(Spacer(1, 20))

    # Custom smaller style for table content
    small_style = ParagraphStyle(
        name='SmallStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10
    )

    # Table Header
    data = [[
        Paragraph("<b>Content</b>", styles['Normal']),
        Paragraph("<b>Prediction</b>", styles['Normal']),
        Paragraph("<b>Confidence</b>", styles['Normal']),
        Paragraph("<b>Date</b>", styles['Normal']),
    ]]

    # Fetch only current user's analyzed results
    analyzed = (
        AnalysisResult.objects
        .filter(article__user=request.user)
        .select_related('article')
        .order_by('-analyzed_at')
    )

    # Add rows
    for item in analyzed:
        content_text = item.article.content[:300]  # limit long content
        data.append([
            Paragraph(content_text, small_style),
            Paragraph(item.prediction, small_style),
            Paragraph(f"{item.confidence_score}%", small_style),
            Paragraph(item.analyzed_at.strftime("%Y-%m-%d"), small_style),
        ])

    # Create table with column widths
    table = LongTable(
        data,
        colWidths=[3*inch, 1*inch, 1*inch, 1*inch],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


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





@login_required
def analysis_history(request):
    results = AnalysisResult.objects.filter(
        article__user=request.user
    ).select_related('article').order_by('-analyzed_at')

    paginator = Paginator(results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total = results.count()
    real_count = results.filter(prediction='Real').count()
    fake_count = results.filter(prediction='Fake').count()
    avg_confidence = results.aggregate(
        Avg('confidence_score')
    )['confidence_score__avg']

    context = {
        'page_obj': page_obj,
        'total': total,
        'real_count': real_count,
        'fake_count': fake_count,
        'avg_confidence': round(avg_confidence, 2) if avg_confidence else 0,
    }

    return render(request, 'analysis_history.html', context)





# =============================================
# Dataset List View
# =============================================
@login_required
def dataset_list(request):
    datasets = Dataset.objects.all().order_by('-uploaded_at')

    context = {
        'datasets': datasets
    }
    return render(request, 'datasets.html', context)


