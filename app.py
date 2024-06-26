from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

TESTING = 0

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


position_landmark_association = db.Table('position_landmarks',
    db.Column('landmark_id', db.Integer, db.ForeignKey('landmark.id'), primary_key=True),
    db.Column('position_id', db.Integer, db.ForeignKey('position.id'), primary_key=True)
)

user_logedin = None

# Entities


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

    def __init__(self, first_name, last_name, pos_level) -> None:
        self.first_name = first_name
        self.pos_level = pos_level
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

class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    cv_id = db.Column(db.Integer, db.ForeignKey('cv.id'), unique=True)
    cv = db.relationship("CV", back_populates="applicant", uselist=False)

    applications = db.relationship('Application', back_populates='applicant', lazy='dynamic')
    offers = db.relationship('Offer', back_populates='applicant', lazy='dynamic')
    
    def __init__(self, first_name, last_name) -> None:
        self.first_name = first_name
        self.last_name = last_name


class CV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experience = db.Column(db.String(450))
    applicant = db.relationship("Applicant", back_populates="cv")
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


# Queries
@app.route('/applicants_with_applications', methods=['GET'])
def get_applicants_with_applications():
    sql_query = text("""
        SELECT DISTINCT a.id, a.first_name, a.last_name
        FROM Applicant a
        JOIN Application app ON a.id = app.applicant_id
    """)

    result = db.session.execute(sql_query)
    applicants_list = [{'id': row[0], 'first_name': row[1], 'last_name': row[2]} for row in result]
    return jsonify(applicants_list)

@app.route('/positions_with_three_applicants', methods=['GET'])
def get_positions_with_three_applicants():
    sql_query = text("""
        SELECT p.id, p.title, p.salary
        FROM Position p
        JOIN Application app ON p.id = app.position_id
        GROUP BY p.id
        HAVING COUNT(app.id) >= 3
    """)
    result = db.session.execute(sql_query)
    positions_list = [{'id': row[0], 'title': row[1], 'salary': row[2]} for row in result]
    return jsonify(positions_list)


@app.route('/applicants_with_offers', methods=['GET'])
def get_applicants_with_offers():
    sql_query = text("""
        SELECT DISTINCT a.id, a.first_name, a.last_name
        FROM Applicant a
        JOIN Offer o ON a.id = o.applicant_id
    """)
    result = db.session.execute(sql_query)
    applicants_list = [{'id': row[0], 'first_name': row[1], 'last_name': row[2]} for row in result]
    return jsonify(applicants_list)


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
    print(universities)
    applicant_universities = []
    for university_name in universities:
        university = University.query.filter_by(name=university_name).first()
        if university:
            applicant_universities.append(university)

    print(applicant_universities)

    cv = CV(experience=experience)
    cv.universities = applicant_universities

    db.session.add(cv)
    db.session.commit()

    applicant = Applicant(first_name=first_name, last_name=last_name)
    applicant.cv = cv

    db.session.add(applicant)
    db.session.commit()

    user_logedin = applicant.id
    return render_template("main.html")





def test_data_insertion():
    numberApplicant = Applicant.query.count()
    numberPosition = Position.query.count()
    numberApplication = Application.query.count()
    numberOffer = Offer.query.count()
    numberCV = CV.query.count()
    numberUniversity = University.query.count()
    numberHRManager = HR_Manager.query.count()

    applicant1 = Applicant(first_name='John', last_name='Doe')
    db.session.add(applicant1)

    position1 = Position(title='Software Engineer', salary=80000)
    db.session.add(position1)

    application1 = Application(recommendation='Good candidate')
    application1.applicant = applicant1
    application1.position = position1
    db.session.add(application1)

    offer1 = Offer(offered_salary=85000, accepted=1)
    offer1.applicant = applicant1
    offer1.position = position1
    db.session.add(offer1)

    cv1 = CV(experience='Bachelor in Computer Science')
    db.session.add(cv1)

    university1 = University(name='Cambridge', location='Cambridge')
    university2 = University(name='Yale', location='New Haven')
    db.session.add_all([university1, university2])

    hr_manager1 = HR_Manager(first_name='Jane', last_name='Smith', pos_level='Senior')
    db.session.add(hr_manager1)

    db.session.commit()

    assert Applicant.query.count() - numberApplicant == 1
    assert Position.query.count() - numberPosition == 1
    assert Application.query.count() - numberApplication == 1
    assert Offer.query.count() - numberOffer == 1
    assert CV.query.count() - numberCV == 1
    assert University.query.count() - numberUniversity == 2
    assert HR_Manager.query.count() - numberHRManager == 1


def test_data_retrieval():
    applicants = Applicant.query.all()
    positions = Position.query.all()
    applications = Application.query.all()
    offers = Offer.query.all()

    assert len(applicants) != 0
    assert len(positions) != 0
    assert len(applications) != 0
    assert len(offers) != 0


def test_data_modification():
    application = Application.query.first()
    application.recommendation = 'Excellent candidate'

    offer = Offer.query.first()
    offer.offered_salary = 90000

    db.session.commit()
    assert Application.query.filter_by(recommendation='Excellent candidate').first() is not None
    assert Offer.query.filter_by(offered_salary=90000).first() is not None

def test_data_deletion():
    numberApplicant = Applicant.query.count()
    numberOffer = Offer.query.count()
    numberApplication = Application.query.count()
    numberPosition = Position.query.count()
    numberCV = CV.query.count()
    numberUniversity = University.query.count()
    numberHRManager = HR_Manager.query.count()

    application = Application.query.first()
    db.session.delete(application)

    offer = Offer.query.first()
    db.session.delete(offer)

    applicant = Applicant.query.first()
    db.session.delete(applicant)
    
    position = Position.query.first()
    db.session.delete(position)
    
    cv = CV.query.first()
    db.session.delete(cv)
    
    university = University.query.first()
    db.session.delete(university)

    manager = HR_Manager.query.first()
    db.session.delete(manager)
    
    
    db.session.commit()
    assert numberApplicant - Applicant.query.count() == 1 
    assert numberOffer - Offer.query.count() == 1
    assert numberApplication - Application.query.count() == 1
    assert numberPosition - Position.query.count() == 1 
    assert numberCV - CV.query.count() == 1
    assert numberUniversity - University.query.count() == 1 
    assert numberHRManager - HR_Manager.query.count() == 1


def data_integrity_testing():
    try:
        invalid_application = Application(recommendation='Good candidate')
        db.session.add(invalid_application)

        invalid_cv = CV(experience=None)
        db.session.add(invalid_cv)

        invalid_university = University(name=None, location='California')
        db.session.add(invalid_university)

        invalid_hr_manager = HR_Manager(first_name=None, last_name='Doe', pos_level='Manager')
        db.session.add(invalid_hr_manager)

        db.session.commit()
    except Exception as e:
        assert 'IntegrityError' in str(e)
        db.session.rollback()

def test_applicant():
    num_applications_before = Application.query.count()

    new_applicant = Applicant(first_name='John', last_name='Doe')
    db.session.add(new_applicant)
    db.session.commit()

    new_position = Position(title='Software Engineer', salary=80000)
    db.session.add(new_position)
    db.session.commit()

    application = Application(recommendation='Good candidate')
    application.applicant = new_applicant
    application.position = new_position
    db.session.add(application)
    db.session.commit()

    num_applications_after = Application.query.count()

    assert num_applications_after - num_applications_before == 1

def test_hr_manager_actions():
    new_applicant = Applicant(first_name='John', last_name='Doe')
    db.session.add(new_applicant)
    db.session.commit()

    new_position = Position(title='Software Engineer', salary=80000)
    db.session.add(new_position)
    db.session.commit()

    new_application = Application()
    new_application.applicant = new_applicant
    new_application.position = new_position
    db.session.add(new_application)
    db.session.commit()

    new_hr_manager = HR_Manager(first_name='Jane', last_name='Smith', pos_level='Senior')
    db.session.add(new_hr_manager)
    db.session.commit()

    new_application.recommendation = 'Highly recommended by HR'

    assert new_application.recommendation == 'Highly recommended by HR'

    new_offer = Offer(offered_salary=90000, accepted=0)
    new_offer.applicant = new_applicant
    new_offer.position = new_position
    db.session.add(new_offer)
    db.session.commit()

    assert Offer.query.filter_by(applicant_id=new_applicant.id, position_id=new_position.id).first() is not None


def run_tests():
    test_data_insertion()
    test_data_retrieval()
    test_data_modification()
    test_data_deletion()
    data_integrity_testing()

    # Applicant related test
    test_applicant()

    # HR Manager related test
    test_hr_manager_actions()


with app.app_context():
    db.create_all()
    initialize_universities()
    initialize_landmark()
    if TESTING:
        run_tests()

if __name__ == "__main__":
    app.run(port=4000,debug=True)
