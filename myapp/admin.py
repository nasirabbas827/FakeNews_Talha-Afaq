from django.contrib import admin
from django import forms
from .models import (
    Profile, Dataset, ModelTrainingLog, ActivityLog,
    NewsArticle, AnalysisResult
)
from .train_model import train_fake_news_model
import csv, io

# =====================================================
# Custom Form to Handle CSV Upload for Datasets
# =====================================================
class DatasetUploadForm(forms.ModelForm):
    dataset_file = forms.FileField(
        required=True,
        help_text="Upload a CSV file with 'Text' and 'label' columns."
    )

    class Meta:
        model = Dataset
        fields = ['dataset_name', 'dataset_file', 'uploaded_by']

    def clean_dataset_file(self):
        file = self.cleaned_data.get('dataset_file')
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Only CSV files are supported.")
        return file

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Optional: Preview CSV rows
        csv_file = self.cleaned_data.get('dataset_file')
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)

        # Optional: Print first 5 rows for verification
        for i, row in enumerate(reader):
            if i >= 5:
                break
            print(f"Text: {row['Text'][:50]}..., Label: {row['label']}")

        if commit:
            instance.save()
        return instance

# =====================================================
# Custom Admin Action: Retrain AI Model
# =====================================================
def retrain_model(modeladmin, request, queryset):
    for dataset in queryset:
        result = train_fake_news_model(dataset.id)
        if result['status'] == 'success':
            modeladmin.message_user(
                request,
                f"Model trained successfully for '{dataset.dataset_name}' | Accuracy: {result['metrics']['accuracy']:.2f}%"
            )
        else:
            modeladmin.message_user(
                request,
                f"Error training model for '{dataset.dataset_name}': {result['message']}",
                level='error'
            )
retrain_model.short_description = "Train AI model on selected datasets"

# =====================================================
# Dataset Admin
# =====================================================
class DatasetAdmin(admin.ModelAdmin):
    form = DatasetUploadForm
    list_display = ('dataset_name', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    actions = [retrain_model]

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

# =====================================================
# ModelTrainingLog Admin
# =====================================================
class ModelTrainingLogAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'accuracy', 'precision', 'recall', 'f1_score', 'trained_at')
    readonly_fields = ('dataset', 'accuracy', 'precision', 'recall', 'f1_score', 'trained_at')

# =====================================================
# Profile Admin
# =====================================================
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture')  # Only existing fields

# =====================================================
# ActivityLog Admin
# =====================================================
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    readonly_fields = ('user', 'action', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'action')

# =====================================================
# NewsArticle Admin
# =====================================================
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'submitted_at')
    readonly_fields = ('submitted_at',)
    search_fields = ('user__username', 'title', 'content')

# =====================================================
# AnalysisResult Admin
# =====================================================
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('article', 'prediction', 'confidence_score', 'model_version', 'analyzed_at')
    readonly_fields = ('article', 'prediction', 'confidence_score', 'model_version', 'analyzed_at')
    list_filter = ('prediction', 'model_version', 'analyzed_at')

# =====================================================
# Register Models
# =====================================================
admin.site.register(Dataset, DatasetAdmin)
admin.site.register(ModelTrainingLog, ModelTrainingLogAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
admin.site.register(NewsArticle, NewsArticleAdmin)
admin.site.register(AnalysisResult, AnalysisResultAdmin)
