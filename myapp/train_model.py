import os
import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from datetime import datetime
from django.conf import settings
from .models import Dataset, ModelTrainingLog

# =====================================================
# Text Preprocessing Function
# =====================================================
def preprocess_text(text):
    """
    Full preprocessing for training:
    - Lowercase
    - Remove URLs, mentions, hashtags
    - Remove numbers
    - Remove punctuation
    - Remove extra whitespace
    """
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)  # remove URLs
    text = re.sub(r'@\w+|#\w+', '', text)  # remove mentions and hashtags
    text = re.sub(r'\d+', '', text)  # remove numbers
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # remove extra spaces
    return text

# =====================================================
# Main Training Function
# =====================================================
def train_fake_news_model(dataset_id):
    try:
        # 1. Get dataset from DB
        dataset_obj = Dataset.objects.get(id=dataset_id)
        dataset_path = os.path.join(settings.MEDIA_ROOT, dataset_obj.dataset_file.name)

        # 2. Read CSV
        df = pd.read_csv(dataset_path)

        # Check required columns
        if 'Text' not in df.columns or 'label' not in df.columns:
            raise ValueError("CSV must contain 'Text' and 'label' columns")

        # 3. Preprocess text
        df['Text'] = df['Text'].astype(str).apply(preprocess_text)
        df['label'] = df['label'].str.strip()

        X = df['Text'].values
        y = df['label'].values

        # 4. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 5. Vectorization
        vectorizer = TfidfVectorizer(
            max_features=5000, ngram_range=(1, 2), stop_words='english'
        )
        X_train_tfidf = vectorizer.fit_transform(X_train)
        X_test_tfidf = vectorizer.transform(X_test)

        # 6. Train Logistic Regression
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train_tfidf, y_train)

        # 7. Predictions & Metrics
        y_pred = clf.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred) * 100
        precision = precision_score(y_test, y_pred, pos_label='Real') * 100
        recall = recall_score(y_test, y_pred, pos_label='Real') * 100
        f1 = f1_score(y_test, y_pred, pos_label='Real') * 100

        # 8. Save model & vectorizer
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"fake_news_model_{timestamp}.joblib"
        vectorizer_filename = f"tfidf_vectorizer_{timestamp}.joblib"

        model_path = os.path.join(settings.MEDIA_ROOT, 'models', model_filename)
        vectorizer_path = os.path.join(settings.MEDIA_ROOT, 'models', vectorizer_filename)

        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        joblib.dump(clf, model_path)
        joblib.dump(vectorizer, vectorizer_path)

        # 9. Log training metrics in DB
        ModelTrainingLog.objects.create(
            dataset=dataset_obj,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            trained_at=datetime.now()
        )

        return {
            "status": "success",
            "model_file": model_filename,
            "vectorizer_file": vectorizer_filename,
            "metrics": {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
