from flask import Flask, request, render_template
import pickle
from PyPDF2 import PdfReader
import re
import os

app = Flask(__name__)

# ------------------- DEBUG (optional) -------------------
print("Current Directory:", os.getcwd())
print("Model Path Exists:", os.path.exists("models/svm_classifier.pkl"))

# ------------------- LOAD MODELS (SAFE) -------------------
try:
    model = pickle.load(open('models/svm_classifier.pkl', 'rb'))
    tfidf = pickle.load(open('models/tfidf_vectorizer.pkl', 'rb'))
    svm_classifier = pickle.load(open('models/job_recoment_svm.pkl', 'rb'))
    tfidf_vectorizer = pickle.load(open('models/job_recoment_tfidf.pkl', 'rb'))
    print("Models Loaded Successfully ✅")
except Exception as e:
    print("Model loading error ❌:", e)

# ------------------- FUNCTIONS -------------------

def pdf_to_text(file):
    reader = PdfReader(file)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def cleanResume(txt):
    txt = re.sub('http\S+\s', ' ', txt)
    txt = re.sub('RT|cc', ' ', txt)
    txt = re.sub('#\S+\s', ' ', txt)
    txt = re.sub('@\S+', ' ', txt)
    txt = re.sub('[%s]' % re.escape("""!'"#$&@();:,.?_^*/\{|}~"""), ' ', txt)
    txt = re.sub(r'[^\x00-\x7f]', ' ', txt)
    txt = re.sub('\s+', ' ', txt)
    return txt

def job_recommendation(resume_text):
    cleaned_text = cleanResume(resume_text)
    vectorized_text = tfidf_vectorizer.transform([cleaned_text])
    return svm_classifier.predict(vectorized_text)[0]

def predict_category(resume_text):
    resume_text = cleanResume(resume_text.lower())
    resume_tfidf = tfidf.transform([resume_text])
    return model.predict(resume_tfidf)[0]

def extract_phone_number(text):
    phone_pattern = r'(\+91[\-\s]?|0)?[6-9]\d{9}'
    match = re.search(phone_pattern, text)
    return match.group() if match else None

def extract_email(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group() if match else None

def extract_skills(text, skills_list):
    skills = []
    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        if re.search(pattern, text, re.IGNORECASE):
            skills.append(skill)
    return skills

# ------------------- SKILLS LIST -------------------
skills_list = [
    "python","java","c++","html","css","javascript","react","node.js",
    "django","flask","machine learning","deep learning","data science",
    "mysql","sql","mongodb","postgresql","git","github","docker",
    "aws","azure","gcp","linux","rest api",
    "communication skills","leadership","teamwork","problem solving"
]

# ------------------- ROUTES -------------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/how_it_works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

@app.route('/pred', methods=['POST'])
def pred():
    if 'resume' not in request.files:
        return render_template("resume.html", message="No file selected")

    file = request.files['resume']

    if file.filename == '':
        return render_template("resume.html", message="No file selected")

    filename = file.filename.lower()

    if filename.endswith('.pdf'):
        text = pdf_to_text(file)
    elif filename.endswith('.txt'):
        text = file.read().decode('utf-8')
    else:
        return render_template("resume.html", message="Invalid file format")

    try:
        predicted_category = predict_category(text)
        recommended_job = job_recommendation(text)
        phone = extract_phone_number(text)
        email = extract_email(text)
        extracted_skills = extract_skills(text, skills_list)
    except Exception as e:
        return render_template("resume.html", message=f"Error: {str(e)}")

    return render_template(
        "resume.html",
        predicted_category=predicted_category,
        recomended_job=recommended_job,
        phone=phone,
        email=email,
        extracted_skills=extracted_skills
    )

# ------------------- RUN -------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)