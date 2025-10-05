from flask import Flask, render_template, request
import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)

# Load trained models and data
vectorizer = joblib.load("models/vectorizer.pkl")
kmeans = joblib.load("models/kmeans_model.pkl")
industry_df = joblib.load("models/industry_data.pkl")
intern_df = joblib.load("models/intern_data.pkl")

# Career cluster information
CLUSTER_NAMES = {
    0: "💻 Tech & Software Development",
    1: "📊 Data Science & Analytics", 
    2: "🎨 Digital Marketing & Design",
    3: "📈 Business & Management",
    4: "🔒 IT & Cybersecurity"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        intern_skills = request.form['skills'].strip().lower()
        if not intern_skills:
            return render_template('result.html', error="Please enter at least one skill.")

        # Transform input
        intern_vec = vectorizer.transform([intern_skills])
        
        # Predict career cluster
        cluster = kmeans.predict(intern_vec)[0]
        cluster_name = CLUSTER_NAMES.get(cluster, "General Professional")
        
        # Compute similarity with industry jobs
        industry_vecs = vectorizer.transform(industry_df['Required_Skills'].fillna(''))
        similarities = cosine_similarity(intern_vec, industry_vecs)[0]
        
        # Get top 5 matches
        top_indices = similarities.argsort()[-5:][::-1]
        top_matches = []
        
        for idx in top_indices:
            top_matches.append({
                'job_title': industry_df.iloc[idx]['Job_Title'],
                'similarity': round(similarities[idx] * 100, 1),
                'required_skills': industry_df.iloc[idx]['Required_Skills']
            })
        
        # Best match analysis
        best_match_idx = similarities.argmax()
        best_job = industry_df.iloc[best_match_idx]['Job_Title']
        required_skills = industry_df.iloc[best_match_idx]['Required_Skills']
        
        if isinstance(required_skills, str):
            required_skill_list = [skill.strip() for skill in required_skills.split(',')]
        else:
            required_skill_list = []
            
        intern_skill_list = [s.strip() for s in intern_skills.split(',')]
        
        missing_skills = [skill for skill in required_skill_list if skill not in intern_skill_list]
        existing_skills = [skill for skill in required_skill_list if skill in intern_skill_list]
        
        if len(required_skill_list) > 0:
            match_percentage = (len(existing_skills) / len(required_skill_list)) * 100
        else:
            match_percentage = 0

        return render_template('result.html',
                               best_job=best_job,
                               match_percentage=round(match_percentage, 1),
                               missing_skills=missing_skills,
                               existing_skills=existing_skills,
                               total_required=len(required_skill_list),
                               career_cluster=cluster_name,
                               top_matches=top_matches,
                               user_skills=intern_skills)

    except Exception as e:
        return render_template('result.html', error=f"Analysis error: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)