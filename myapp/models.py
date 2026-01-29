from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# =====================================================
# Dataset Management
# =====================================================
class Dataset(models.Model):
    dataset_name = models.CharField(max_length=150)
    dataset_file = models.FileField(upload_to='datasets/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.dataset_name


# =====================================================
# Model Training Logs
# =====================================================
class ModelTrainingLog(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2)
    precision = models.DecimalField(max_digits=5, decimal_places=2)
    recall = models.DecimalField(max_digits=5, decimal_places=2)
    f1_score = models.DecimalField(max_digits=5, decimal_places=2)
    trained_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Training {self.id} - Accuracy {self.accuracy}%"


# =====================================================
# Activity Logs
# =====================================================
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.action}"
    

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# News Article
class NewsArticle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='news_articles')
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Article {self.id} by {self.user.username}"


# AI Analysis Result
class AnalysisResult(models.Model):
    PREDICTION_CHOICES = (
        ('Real', 'Real'),
        ('Fake', 'Fake'),
    )

    article = models.OneToOneField(NewsArticle, on_delete=models.CASCADE, related_name='analysis')
    prediction = models.CharField(max_length=10, choices=PREDICTION_CHOICES)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    model_version = models.CharField(max_length=50)
    analyzed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.prediction} ({self.confidence_score}%)"
