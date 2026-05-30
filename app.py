from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os
from pathlib import Path
import zipfile
import tempfile
from io import BytesIO

app = Flask(__name__)
db_path = Path(__file__).parent / "data" / "voting.db"
os.makedirs(db_path.parent, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path.as_posix()}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'offline-voting-key'
db = SQLAlchemy(app)

with app.app_context():
        setup()

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    max_voters = db.Column(db.Integer, nullable=False, default=100)
    candidates = db.relationship('Candidate', backref='class_', lazy=True)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    votes = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)

active_class_id = None

def setup():
    os.makedirs("exports", exist_ok=True)
    db.create_all()

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global active_class_id
    if request.method == 'POST':
        if 'class_name' in request.form:
            class_name = request.form['class_name']
            candidate_names = request.form.getlist('candidate_names')
            max_voters = int(request.form.get('max_voters', 100))
            if class_name and candidate_names:
                new_class = Class(name=class_name, max_voters=max_voters)
                db.session.add(new_class)
                db.session.flush()
                for name in candidate_names:
                    if name.strip():
                        db.session.add(Candidate(name=name.strip(), class_id=new_class.id))
                db.session.commit()
        elif 'set_active_class' in request.form:
            active_class_id = int(request.form['set_active_class'])
    
    classes = Class.query.all()
    selected_class = next((cls for cls in classes if cls.id == active_class_id), None)
    max_votes = selected_class.max_voters if selected_class else 0

    return render_template('admin.html', classes=classes, active_class_id=active_class_id, max_votes=max_votes)

@app.route('/user', methods=['GET'])
def user():
    if active_class_id is None:
        return "No class is currently open for voting. Please contact admin."
    candidates = Candidate.query.filter_by(class_id=active_class_id).all()
    classes = Class.query.all()
    selected_class = next((cls for cls in classes if cls.id == active_class_id), None)
    max_votes = selected_class.max_voters if selected_class else 0
    return render_template('class_vote.html', candidates=candidates, class_id=active_class_id, classes=classes, max_votes=max_votes)

@app.route('/vote', methods=['POST'])
def vote():
    if active_class_id is None:
        return jsonify({'status': 'error', 'message': 'Voting is not active'}), 400

    candidate_id = request.json.get('candidate_id')
    if candidate_id:
        class_obj = Class.query.get(active_class_id)
        total_votes = Vote.query.join(Candidate).filter(Candidate.class_id == active_class_id).count()

        if total_votes >= class_obj.max_voters:
            return jsonify({'status': 'error', 'message': 'Maximum number of voters reached'}), 403

        db.session.add(Vote(candidate_id=int(candidate_id)))
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Vote registered successfully'})
    
    return jsonify({'status': 'error', 'message': 'Invalid candidate ID'}), 400

@app.route('/live-results')
def live_results():
    if active_class_id is None:
        return jsonify({"error": "No active class selected"}), 400
    candidates = Candidate.query.filter_by(class_id=active_class_id).all()
    results = [{"name": c.name, "votes": len(c.votes)} for c in candidates]
    return jsonify(results)

@app.route('/add-candidate', methods=['POST'])
def add_candidate():
    if active_class_id is None:
        return redirect(url_for('admin'))

    name = request.form.get('candidate_name')
    if name:
        existing = Candidate.query.filter_by(name=name, class_id=active_class_id).first()
        if not existing:
            new_candidate = Candidate(name=name, class_id=active_class_id)
            db.session.add(new_candidate)
            db.session.commit()
    return redirect(url_for('admin'))
@app.route('/reset_votes', methods=['POST'])
def reset_votes():
    class_id = request.form.get('class_id')
    if class_id:
        candidates = Candidate.query.filter_by(class_id=class_id).all()
        for candidate in candidates:
            Vote.query.filter_by(candidate_id=candidate.id).delete()
        db.session.commit()
        return redirect(url_for('admin'))
    return "Invalid class ID", 400

@app.route('/export_results', methods=['POST'])
def export_results():
    from datetime import datetime
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import cm
    from reportlab.lib import colors

    classes = Class.query.all()

    if not classes:
        return "No classes found. Nothing to export."

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

        for cls in classes:

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                pdf_path = temp_pdf.name

            total_votes = sum(len(c.votes) for c in cls.candidates)
            max_voters = cls.max_voters
            votes_remaining = max(0, max_voters - total_votes)

            table_data = [["Candidate Name", "Votes"]]

            for candidate in cls.candidates:
                table_data.append([
                    candidate.name,
                    str(len(candidate.votes))
                ])

            try:
                doc = SimpleDocTemplate(
                    pdf_path,
                    pagesize=A4,
                    rightMargin=2 * cm,
                    leftMargin=2 * cm,
                    topMargin=2 * cm,
                    bottomMargin=2 * cm
                )

                styles = getSampleStyleSheet()
                elements = []

                header_style = ParagraphStyle(
                    name='HeaderStyle',
                    fontSize=20,
                    leading=26,
                    alignment=TA_CENTER,
                    textColor=colors.white,
                    backColor=colors.darkblue,
                    spaceAfter=12,
                    spaceBefore=6
                )

                elements.append(
                    Paragraph(
                        f"<b>VOTING REPORT - {cls.name.upper()}</b>",
                        header_style
                    )
                )

                sub_style = ParagraphStyle(
                    name='SubInfo',
                    fontSize=10,
                    textColor=colors.grey,
                    spaceAfter=6,
                    alignment=TA_CENTER
                )

                elements.append(
                    Paragraph(
                        f"Generated on: {now}",
                        sub_style
                    )
                )

                elements.append(Spacer(1, 12))

                summary_data = [
                    ["Total Votes Cast", str(total_votes)],
                    ["Maximum Voters", str(max_voters)],
                    ["Votes Remaining", str(votes_remaining)]
                ]

                summary_table = Table(
                    summary_data,
                    colWidths=[150, 200]
                )

                summary_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))

                elements.append(summary_table)
                elements.append(Spacer(1, 24))

                result_table = Table(
                    table_data,
                    colWidths=[300, 100]
                )

                result_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.whitesmoke, colors.lightgrey]),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))

                elements.append(
                    Paragraph(
                        "<b>Candidate-wise Vote Count</b>",
                        styles['Heading3']
                    )
                )

                elements.append(Spacer(1, 10))
                elements.append(result_table)

                doc.build(elements)

                pdf_name = f"{cls.name.replace(' ', '_')}_results.pdf"

                zip_file.write(pdf_path, pdf_name)

                os.remove(pdf_path)

            except Exception as e:
                return f"Error creating PDF for {cls.name}: {str(e)}"

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='Voting_Results.zip'
    )

with app.app_context():
    setup()

if __name__ == '__main__':
    app.run()
