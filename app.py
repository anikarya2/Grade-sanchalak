import os
import re
from flask import Flask, request, render_template, session, redirect, url_for
from PyPDF2 import PdfReader
import docx

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# List of stopwords (optional - can be expanded as needed)
STOPWORDS = {"the", "is", "in", "and", "or", "a", "to", "of", "for", "on", "with", "this", "that", "it"}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle Keyword Generation
        if 'generate_keywords' in request.form:
            if 'file' in request.files:
                file = request.files['file']
                if file:
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(file_path)

                    file_text = extract_text_from_file(file_path)

                    # Generate keywords from file content
                    generated_keywords = generate_keywords_from_text(file_text)
                    return render_template('index.html', generated_keywords=generated_keywords)

        # Handle Assignment Checking
        if 'check_assignments' in request.form:
            keywords_input = request.form.get('keywords', '')
            keywords = [kw.strip() for kw in keywords_input.split(',')] if keywords_input else []

            results = []

            if 'files' in request.files:
                files = request.files.getlist('files')

                for file in files:
                    if file:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                        file.save(file_path)

                        assignment_text = extract_text_from_file(file_path)

                        # Calculate keyword matching
                        keyword_count = {kw: assignment_text.lower().count(kw.lower()) for kw in keywords}
                        matching_keywords = [kw for kw, count in keyword_count.items() if count > 0]
                        non_matching_keywords = [kw for kw in keywords if kw not in matching_keywords]

                        matched_keywords_count = len(matching_keywords)
                        total_keywords = len(keywords) if keywords else 1  # Avoid division by zero

                        percentage = (matched_keywords_count / total_keywords) * 100

                        # Append results for each file
                        results.append({
                            'filename': file.filename,
                            'matching_keywords': matching_keywords,
                            'non_matching_keywords': non_matching_keywords,
                            'score': f"{matched_keywords_count} out of {total_keywords}",
                            'percentage': percentage
                        })

            session['results'] = results
            return redirect(url_for('index'))

    results = session.pop('results', None)
    return render_template('index.html', results=results)


def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def extract_text_from_file(file_path):
    """Detect file type and extract text accordingly"""
    if file_path.endswith('.txt'):
        return extract_text_from_txt(file_path)
    elif file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    return ""


def generate_keywords_from_text(text):
    """Extract up to 50 keywords from text"""
    words = re.findall(r'\b\w+\b', text.lower())  # Extract words
    filtered_words = [word for word in words if word not in STOPWORDS and len(word) > 2]  # Remove stopwords and short words
    unique_keywords = list(set(filtered_words))  # Remove duplicates
    return unique_keywords[:50]  # Limit to 50 keywords


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
