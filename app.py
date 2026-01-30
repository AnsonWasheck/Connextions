from flask import Flask, render_template, request, jsonify, redirect, url_for
import logic

app = Flask(__name__)

@app.route('/')
def index():
    members = logic.get_all_people()
    return render_template('index.html', members=members)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"answer": "Please ask something about your network."})
    
    try:
        answer = logic.process_ai_query(query)
        return jsonify({"answer": answer})
    except Exception as e:
        print("Search error:", e)  # This shows in terminal
        return jsonify({"answer": f"Backend error: {str(e)}"})

@app.route('/add', methods=['POST'])
def add():
    logic.add_person({
        "full_name": request.form.get('full_name'),
        "contact_info": request.form.get('contact_info'),
        "job_title": request.form.get('job_title'),
        "company": request.form.get('company'),
        "industry": request.form.get('industry'),
        "sector": request.form.get('sector'),
        "skills_experience": request.form.get('skills_experience'),
        "ai_summary": request.form.get('ai_summary'),
        "ai_rating": request.form.get('ai_rating', 5),
        "rating_momentum": request.form.get('rating_momentum'),
        "key_accomplishments": request.form.get('key_accomplishments'),
        "relationship_status": request.form.get('relationship_status'),
        "days_since_contact": request.form.get('days_since_contact', 0),
        "mutual_connections": request.form.get('mutual_connections'),
        "personal_notes": request.form.get('personal_notes')
    })
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)