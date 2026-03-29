import joblib
import os
import numpy as np
from textblob import TextBlob

# Load pkl files once at startup
# Assuming the files are in the same directory as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TFIDF_PATH = os.path.join(BASE_DIR, "tfidf_vectorizer.pkl")
MODEL_PATH = os.path.join(BASE_DIR, "best_complaint_classifier.pkl")

tfidf = joblib.load(TFIDF_PATH)
model = joblib.load(MODEL_PATH)

TOPIC_MAPPING = {
    0: "Payment Services",           # Previously Bank account
    1: "Others",                     # Previously Credit card
    2: "Mortgages/loans",            # Previously Payment Services
    3: "Bank account services",      # Previously Others
    4: "Credit card / Prepaid card", # Previously Mortgages/loans
    5: "Theft/Dispute"               # Unchanged index but different features
}

def predict_all(complaint_text):
    """
    Predicts both topic and priority of a complaint.
    
    Returns: (predicted_topic, predicted_priority, priority_rank)
    """
    # Transform text
    text_vector = tfidf.transform([complaint_text])
    
    # Predict probabilities (Confidence Thresholding)
    probs = model.predict_proba(text_vector)[0]
    max_prob = np.max(probs)
    idx = int(np.argmax(probs))
    
    # Financial Word Density Check
    known_words_count = (text_vector > 0).sum()
    
    # Domain Filter: Ensure at least one core banking term exists
    domain_keywords = [
        "bank", "account", "credit", "card", "loan", "mortgage", "payment", 
        "transaction", "money", "charge", "fraud", "theft", "stolen", "dispute", 
        "fee", "branch", "deposit", "balance", "checking", "savings", "interest", 
        "refund", "overdraft", "bill", "debt", "cash", "check", "app"
    ]
    text_lower = complaint_text.lower()
    has_domain_word = any(word in text_lower for word in domain_keywords)
    
    # Get Topic
    if max_prob < 0.40 or known_words_count < 4 or not has_domain_word:
        predicted_topic = "Unknown / Manual Review Required"
    else:
        predicted_topic = TOPIC_MAPPING.get(idx, "Others")
    
    # Define priority based on topic/index
    # 2 Mortgages -> High (1)
    # 5 Theft -> High (1)
    # 0 Payment -> Medium (2)
    # 3 Bank Account -> Medium (2)
    # 4 Credit Card -> Medium (2)
    # 1 Others -> Low (3)
    
    if predicted_topic == "Unknown / Manual Review Required" or idx in [2, 5]:
        predicted_priority, priority_rank = "High", 1
    elif idx in [0, 3, 4]:
        predicted_priority, priority_rank = "Medium", 2
    else:
        predicted_priority, priority_rank = "Low", 3
        
    # Sentiment-Boosted Priority
    # If the text is extremely negative, automatically bump the priority to High
    blob = TextBlob(complaint_text)
    if blob.sentiment.polarity < -0.3:
        predicted_priority, priority_rank = "High", 1
        
    # High-Risk Keyword Override
    # Financial ML models often struggle when "Bank Account" strings overpower "Theft" strings.
    # We use an industry-standard rule-based expert override for critical security issues.
    critical_keywords = ["unauthorized", "stolen", "stole", "fraud", "hacked", "identity theft", "scam"]
    text_lower = complaint_text.lower()
    if any(keyword in text_lower for keyword in critical_keywords):
        predicted_priority, priority_rank = "High", 1

    return (predicted_topic, predicted_priority, priority_rank)

def predict_priority(complaint_text):
    """Legacy support - returns priority tuple"""
    topic, priority, rank = predict_all(complaint_text)
    return priority, rank
