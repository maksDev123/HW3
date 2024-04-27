from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


position_landmark_association = db.Table('position_landmarks',
    db.Column('landmark_id', db.Integer, db.ForeignKey('landmark.id'), primary_key=True),
    db.Column('position_id', db.Integer, db.ForeignKey('position.id'), primary_key=True)
)

user_logedin = None

class Application(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    recommendation = db.Column(db.String(500))
    id_applicant= db.Column(db.Integer, db.ForeignKey('applicant.id'))
    id_postion= db.Column(db.Integer, db.ForeignKey('company.id'))

class Landmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    def __init__(self, title, location) -> None:
        self.title = title
        self.location = location

class Position(db.Model):
    id = db.Column(db.Integer, db.ForeignKey("position.id"),primary_key=True)
    title = db.Column(db.String(100))
    salary = db.Column(db.Integer())
    landmark = db.relationship('Landmark', secondary=position_landmark_association, backref=db.backref('cvs', lazy='dynamic'))
    def __init__(self, title, salary) -> None:
        self.title = title
        self.salary = salary
class Company(db.Model):
    id = db.Column(db.Integer, db.ForeignKey("company.id"), primary_key=True)
    name = db.Column(db.String(100))
    nEmployes = db.Column(db.Integer)
    def __init__(self, name, nEmployes):
        self.name = name
        self.nEmployes = nEmployes




class HR_Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    pos_level = db.Column(db.String(45))
    id_company = db.Column(db.Integer, db.ForeignKey('company.id'))

    def __init__(self, first_name, last_name) -> None:
        self.first_name = first_name
        self.last_name = last_name

cv_universities_association = db.Table('cv_universities',
    db.Column('cv_id', db.Integer, db.ForeignKey('cv.id'), primary_key=True),
    db.Column('university_id', db.Integer, db.ForeignKey('university.id'), primary_key=True)
)

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))

    def __init__(self, name, location):
        self.name = name
        self.location = location

class CV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experience = db.Column(db.String(450))
    universities = db.relationship('University', secondary=cv_universities_association, backref=db.backref('cvs', lazy='dynamic'))

    def __init__(self, experience) -> None:
        self.experience = experience

class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    id_cv = db.Column(db.Integer, db.ForeignKey('cv.id'))

    def __init__(self, first_name, last_name) -> None:
        self.first_name = first_name
        self.last_name = last_name

def initialize_universities():
    universities_data = [
        {"name": "Harvard", "location": "Massachusetts"},
        {"name": "Oxford", "location": "California"},
        {"name": "UCU", "location": "Lviv"},
        {"name": "LNU", "location": "Lviv"},
        {"name": "KPI", "location": "Lviv"},
    ]

    for university_info in universities_data:
        university = University(**university_info)
        db.session.add(university)

    db.session.commit()



def initialize_landmark():
    landmark_data = [
        {"title": "Eiffel Tower", "location": "Paris"},
        {"title": "Statue of Liberty", "location": "New York"},
        {"title": "Colosseum", "location": "Rome"},
        {"title": "Sydney Opera House", "location": "Sydney"},
    ]

    for landmark_info in landmark_data:
        landmark = Landmark(**landmark_info)
        db.session.add(landmark)

    db.session.commit()

# Endpoints
@app.route('/post_position_form', methods=['GET', 'POST'])
def register_position():
    if request.method == 'POST':
        title = request.form['title']
        salary = request.form['salary']
        landmarks = request.form.getlist('landmark[]')

        new_position = Position(title=title, salary=salary)

        for landmark_title in landmarks:
            landmark = Landmark.query.filter_by(title=landmark_title).first()
            new_position.landmark.append(landmark)

        db.session.add(new_position)
        db.session.commit()

        return "Position added successfully!"
    return "Incorect request type"

@app.route('/positions')
def show_positions():
    positions = Position.query.all()
    return render_template('positions.html', positions=positions)

@app.route('/application')
def get_applications():
    applications = Application.query.all()
    return render_template('positions.html', positions=applications)



@app.route('/positions/<int:position_id>', methods=['POST'])
def handle_position_request(position_id):
 
    applicantion = Application()
    applicantion.id_applicant = user_logedin
    applicantion.id_position = position_id
    db.session.add(applicantion)
    db.session.commit()
    return "Application received"

@app.route("/post_position")
def post_position():
    return render_template("post_positions.html")

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def submit_form():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    experience = request.form['experience']
    universities = request.form.getlist('university[]')

    if "Choose University" in universities:
        universities.remove("Choose University")

    applicant_universities = []
    for university_name in universities:
        university = University.query.filter_by(name=university_name).first()
        if university:
            applicant_universities.append(university)


    cv = CV(experience=experience)
    cv.universities = applicant_universities

    db.session.add(cv)
    db.session.commit()

    applicant = Applicant(first_name=first_name, last_name=last_name)
    applicant.id_cv = cv.id

    db.session.add(applicant)
    db.session.commit()

    user_logedin = applicant.id
    return 'Form submitted successfully!'

with app.app_context():
    db.create_all()
    initialize_universities()
    initialize_landmark()

if __name__ == "__main__":
    app.run(debug=True)
