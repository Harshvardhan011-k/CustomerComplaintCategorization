# Consumer Complaint Categorization System

An industry-level NLP web application that automatically categorizes consumer financial complaints and assigns priority levels using advanced Machine Learning models.

## Features
- **Machine Learning Classification**: Accurately maps incoming complaints into topics like Credit cards, Mortgages, Bank Account Services, and Payment Services.
- **Auto-Triage & Alerts**: Simulates an enterprise-level triage system by immediately alerting users if their complaint is flagged for fraud or manual review.
- **Confidence & Domain Filters**: Employs an intelligent vocabulary density check to reject meaningless gibberish and off-topic messages before they hit the ML pipeline.
- **Sentiment-Boosted Priority**: Analyzes the emotional sentiment of the text using `TextBlob`. Highly negative or distressed complaints artificially upgrade their priority to **High**.
- **Rule-Based Triage Overrides**: Scans for high-risk critical terminology (like "fraud" or "unauthorized") to immediately lock high-priority status onto security-related cases without overriding the core ML topic.
- **Owner Dashboard**: Features a data-rich analytics dashboard to track real-time metrics, categorize recent activities, and visualize the distribution of complaint topics.
- **Supabase Integration**: Backend data storage and retrieval is fully integrated with Supabase PostgreSQL.

## Workflow

1. A user submits a financial complaint.
2. The system checks for domain-specificity. If it fails, it is marked as `Unknown`.
3. If it passes, the TF-IDF Vectorizer and Logistic Regression model assign a topic and calculate the prediction confidence.
4. Sentiment analysis is layered on top to adjust priority.
5. The complaint is stored in Supabase and displayed dynamically on the Owner Dashboard for triage.

## Setup & Installation

1. Clone this repository.
2. Install the core dependencies (ensure you have `.pkl` model files in the root):
   ```bash
   pip install flask textblob supabase joblib scikit-learn numpy flask-bcrypt python-dotenv
   ```
3. Create a `.env` file with your credentials:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SECRET_KEY=your_flask_secret
   ```
4. Run the Flask application:
   ```bash
   python app.py
   ```

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: HTML5, Vanilla CSS, JS
- **Database**: Supabase / PostgreSQL
- **Machine Learning**: Scikit-Learn (LogisticRegression, TfidfVectorizer), TextBlob, Numpy
