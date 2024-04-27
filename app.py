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
class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    id_cv = db.Column(db.Integer, db.ForeignKey('cv.id'))
    applications = db.relationship('Application', back_populates='applicant', lazy='dynamic')
    offers = db.relationship('Offer', back_populates='applicant', lazy='dynamic')
    
    def __init__(self, first_name, last_name) -> None:
        self.first_name = first_name
        self.last_name = last_name


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recommendation = db.Column(db.String(500))
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicant.id'), unique=False, nullable=False)
    applicant = db.relationship("Applicant", back_populates="applications")

    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), unique=False, nullable=False)
    position = db.relationship("Position", back_populates="applications")

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offered_salary = db.Column(db.String(500))
    accepted = db.Column(db.Integer)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicant.id'), unique=False, nullable=False)
    applicant = db.relationship("Applicant", back_populates="offers")

    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), unique=False, nullable=False)
    position = db.relationship("Position", back_populates="offers")

    # position_id = db.Column(db.Integer, db.ForeignKey('position.id'), unique=False, nullable=False)
    # position = db.relationship("Position", back_populates="offers")


class Landmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    def __init__(self, title, location) -> None:
        self.title = title
        self.location = location

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    salary = db.Column(db.Integer())
    landmark = db.relationship('Landmark', secondary=position_landmark_association, backref=db.backref('cvs', lazy='dynamic'))
    applications = db.relationship('Application', back_populates='position', lazy='dynamic')
    offers = db.relationship('Offer', back_populates='position', lazy='dynamic')
    
    def __init__(self, title, salary) -> None:
        self.title = title
        self.salary = salary

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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

@app.route('/', methods = ['GET', 'POST'])
def main_page():
    return render_template("main.html")

@app.route('/login', methods=['POST'])
def login():
    global user_logedin
    first_name = request.form["first_name"]
    aplicant = Applicant.query.filter_by(first_name = first_name).first()
    print(first_name)
    print(aplicant)
    if not aplicant:
        return "No user with such name"
    print(aplicant)
    user_logedin = aplicant.id
    return render_template("main.html")


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

        return render_template("main.html")
    return "Incorect request type"

@app.route('/positions')
def show_positions():
    positions = Position.query.all()
    return render_template('positions.html', positions=positions)

@app.route('/applications')
def get_applications():
    applications = Application.query.filter(Application.recommendation == None).all()
    return render_template('applications.html', applications = applications)

@app.route('/applications_filled')
def get_applications_filled():
    applications = Application.query.filter(Application.recommendation != "").all()
    return render_template('applications_filled.html', applications = applications)


@app.route('/applications_filled/<int:application_id>', methods=['POST'])
def send_offer(application_id):
    offered_salary = request.json['salary']
    offer = Offer(offered_salary = offered_salary)
    offer.accepted = 0
    application = Application.query.filter_by(id = application_id).first()
    applicant = application.applicant
    position = application.position
    offer.applicant = applicant
    offer.position = position
    db.session.add(offer)
    db.session.commit()
    return "Application received"


@app.route('/acceptance/<int:offer_id>', methods=['POST'])
def update_offer(offer_id):
    accept = request.json['accept']
    offer = Offer(id = offer_id)
    offer.accepted =  1 if accept else -1
    db.session.commit()
    return "Application received"


@app.route('/applications/<int:application_id>', methods=['POST'])
def update_recommendations(application_id):
    try:
        recommendation = request.json['recommendation']
        application = Application.query.get(application_id)

        if application:
            application.recommendation = recommendation
            db.session.commit()
            return "Recommendation updated successfully", 200
        else:
            return "Application not found", 404
    except Exception as e:
        return str(e), 500

# @app.route('/applications/<int:application_id>', methods=['POST'])
# def update_recommendations(application_id):

#     recommendation = request.json['recommendation']
#     application = Application.query.filter_by(id = application_id).first()
#     application.recommedation = recommendation
#     db.session.add(application)
#     db.session.commit()
#     return "Application received"


@app.route('/positions/<int:position_id>', methods=['POST'])
def handle_position_request(position_id):
    print(position_id)
    print("-------------------------")
    applicantion = Application()
    aplicant = Applicant.query.filter_by(id = user_logedin).first()
    position = Position.query.filter_by(id = position_id).first()
    applicantion.applicant = aplicant
    applicantion.position = position
    db.session.add(applicantion)
    db.session.commit()
    return "Application received"

@app.route("/offers")
def get_offers():
    offers = Offer.query.filter_by(id = user_logedin).all()
    return render_template("offers.html", offers = offers)

@app.route("/post_position")
def post_position():
    return render_template("post_positions.html")

@app.route("/login_form")
def login_form():
    return render_template("login.html")

@app.route("/register")
def hello_world():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def submit_form():
    global user_logedin
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
    return render_template("main.html")

with app.app_context():
    db.create_all()
    initialize_universities()
    initialize_landmark()

if __name__ == "__main__":
    app.run(port=4000,debug=True)
