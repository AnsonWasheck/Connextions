from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import logic

app = Flask(__name__)
app.secret_key = "your-secret-key-change-me-please"   # ← required for flash messages

# Optional: better static file handling in debug (not strictly needed)
# app.static_folder = 'static'

@app.route('/')
def index():
    members = logic.get_all_people()
    return render_template('index.html', members=members)


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()   # safer than request.json in some edge cases
    if not data:
        return jsonify({"answer": "Invalid request"}), 400

    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"answer": "Please ask something about your network."}), 400
    
    try:
        answer = logic.process_ai_query(query)
        return jsonify({"answer": answer})
    except Exception as e:
        import traceback
        traceback.print_exc()           # better debugging in terminal
        return jsonify({"answer": "Sorry, something went wrong on the server side."}), 500


@app.route('/add', methods=['POST'])
def add():
    try:
        person_data = {
            "full_name":        request.form.get('full_name'),
            "contact_info":     request.form.get('contact_info'),
            "job_title":        request.form.get('job_title'),
            "company":          request.form.get('company'),
            "industry":         request.form.get('industry'),
            "sector":           request.form.get('sector'),
            "skills_experience":request.form.get('skills_experience'),
            "ai_summary":       request.form.get('ai_summary'),
            "ai_rating":        int(request.form.get('ai_rating', 5)),
            "rating_momentum":  request.form.get('rating_momentum'),
            "key_accomplishments": request.form.get('key_accomplishments'),
            "relationship_status": request.form.get('relationship_status'),
            "days_since_contact":  int(request.form.get('days_since_contact', 0)),
            "mutual_connections":  request.form.get('mutual_connections'),
            "personal_notes":      request.form.get('personal_notes')
        }

        logic.add_person(person_data)
        flash("Connection added successfully!", "success")   # nice feedback
        return redirect(url_for('index'))

    except ValueError as ve:
        # e.g. invalid int conversion
        flash(f"Invalid input: {ve}", "error")
        return redirect(url_for('index'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash("Failed to add connection. Please try again.", "error")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')   # ← host='0.0.0.0' useful if testing from phone/tablet