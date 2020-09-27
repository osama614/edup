import os 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView , helpers, expose
from flask_admin.contrib.sqla import ModelView 
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
from flask import redirect, url_for, request



database_path = os.environ.get('SQLALCHEMY_DATABASE_URI')

db = SQLAlchemy()
migrate = Migrate()
admins = Admin(base_template='my_master.html')
login_manager = LoginManager()

'''
setup_db(app)
    binds a flask application and a SQLAlchemy service
'''
def setup_db(app, database_path=database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    migrate.init_app(app, db)
    admins.init_app(app, index_view=MyAdminIndexView())
    login_manager.init_app(app)


class ViewMixin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def is_visible(self):
        return current_user.is_authenticated


class SchoolYear(db.Model):

    __tablename__ = 'schoolyear'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    students = db.relationship('Student', backref= 'study_year')
    exams = db.relationship('Exam', backref='study_year')
    groups = db.relationship('Group', backref='study_year')
    questions = db.relationship('Question', backref='study_year')

    def __repr__(self):
        return f'<name: {self.name}'

    def format(self):

        return {
            "id": self.id,
            "name": self.name
        }    

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    teachers = db.relationship('Teacher', backref='subject')
    questions = db.relationship('Question', backref='subject')
    exams = db.relationship('Exam', backref='subject')

    def __repr__(self):
        return f'<name: {self.name}'

    def format(self):

        return {
            "id": self.id,
            "name": self.name
        }        



class AuthMixin():

    is_active = db.Column(db.Boolean, default=True, server_default='true')

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active


class Center(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))


class CenterView(ViewMixin, ModelView):
    form_columns   = ['teacher_id', 'student_id', 'group_id']    
    can_view_details = True 
    can_export = True

class Result(db.Model):

      id = db.Column(db.Integer, primary_key=True)
      exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
      title = db.Column(db.String(50))
      start_date = db.Column(db.DateTime)
      student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
      teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
      total_grade = db.Column(db.Float)


      def insert(self):
        db.session.add(self)
        db.session.commit()

      def format(self):

        return {
            "id": self.id,
            "title": self.title,
            "start_date": self.start_date,
            "total_grade": self.total_grade
        }    


class ResultView(ViewMixin, ModelView):
    form_columns   = ['exam_id', 'student_id', "teacher_id", "total_grade", "title", "start_date"]    
    can_view_details = True 
    can_export = True

class Teacher(AuthMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    mobile = db.Column(db.Text, unique=True, nullable=False)
    image_url = db.Column(db.Text)
    roles = db.Column(db.Text, nullable=False, default= 'teacher')
    Subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    exams = db.relationship('Exam', backref='exam_owner')
    groups = db.relationship('Group', backref='group_owner')
    questions = db.relationship('Question', backref='question_owner')
    results = db.relationship('Result', backref='teacher')
    students = db.relationship('Student', secondary= 'center', lazy='dynamic',
        backref=db.backref('teachers', lazy=True))

    def __repr__(self):
        return f'<name: {self.username}'

    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):

        return {
            "id": self.id,
            "username": self.username,
            "mobile": self.mobile,
            "image_url": self.image_url 
        } 

    def format2(self):

        return {
            "id": self.id,
            "username": self.username,
        }           


class Student(AuthMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    mobile = db.Column(db.Text, unique=True, nullable=False )
    has_exam = db.Column(db.Boolean, nullable=False, default=False)
    exams_num = db.Column(db.Integer, nullable=False, default=0)
    teachers_num = db.Column(db.Integer, nullable=False, default=0)
    roles = db.Column(db.Text, nullable=False, default= 'student' )
    school_year_id = db.Column(db.Integer, db.ForeignKey('schoolyear.id'))

    exams = db.relationship('Exam', secondary= 'exam_room',
        backref=db.backref('students', lazy=True))

    results = db.relationship('Exam', secondary= 'result', lazy='dynamic',
        backref=db.backref('students_took_the_exam', lazy=True))

        

    def __repr__(self):
        return f'<name: {self.username}'    

    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            "id": self.id,
            "fname": self.fname,
            "lname": self.lname,
            "mobile": self.mobile,
            "has_exam": self.has_exam,
            "exams_num": self.exams_num
        }    




class Operator(AuthMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    roles = db.Column(db.Text, nullable=False, default= 'admin')

    def __repr__(self):
        return f'<name: {self.username}'

    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()        


class Assistant(AuthMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    roles = db.Column(db.Text, nullable=False, default= 'assistant')


    def __repr__(self):
        return f'<name: {self.username}'

    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()        


class Question(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    question_head = db.Column(db.Text)
    image_url = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    correct_answer_image_url = db.Column(db.Text)
    answer1 = db.Column(db.Text)
    answer1_image_url = db.Column(db.Text)
    answer2 = db.Column(db.Text)
    answer2_image_url = db.Column(db.Text)
    answer3 = db.Column(db.Text)
    answer3_image_url = db.Column(db.Text)
    grade = db.Column(db.Float)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id')) 
    school_year_id = db.Column(db.Integer, db.ForeignKey('schoolyear.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id')) 
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))

    def __repr__(self):
        return f'<name: {self.question_head}'


    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()   

    def format(self):
        
        return {
            "id": self.id,
            "text":self.question_head,
            "img": self.image_url,
            "choiceA":{
                "text":self.correct_answer,
                "img": self.correct_answer_image_url
                },
            "choiceB":{
                "text": self.answer1,
                "img": self.answer1_image_url
                },
            "choiceC":{
                "text": self.answer2,
                "img": self.answer2_image_url
                },
            "choiceD":{
                "text": self.answer3,
                "img": self.answer3_image_url
                },
            "answer" : "choiceA"
}
        

class ExamRoom(db.Model):

    __tablename__ = 'exam_room'
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'),primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    

class Exam(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    total_time = db.Column(db.Integer)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    questions = db.relationship('Question', backref='exam')
    school_year_id = db.Column(db.Integer, db.ForeignKey('schoolyear.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    

    def __repr__(self):
        return f'<name: {self.title}'


    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()    

    def format(self):

        return {
            "id": self.id,
            "title": self.title,
            "total_time": self.total_time,
            "start_date": f'{self.start_date}',
            "end_date": f'{self.end_date}',           
        }
        
    def format2(self):
        return  {
            "id": self.id,
            "title": self.title,
        }       


group_exam = db.Table('group_exam',
    db.Column('exam_id', db.Integer, db.ForeignKey('exam.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    )


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    school_year_id = db.Column(db.Integer, db.ForeignKey('schoolyear.id'))
    students = db.relationship('Student', secondary= 'center',
        backref=db.backref('groups', lazy=True))

    exams = db.relationship('Exam', secondary= 'group_exam',
        backref=db.backref('groups', lazy=True))    

      

    def insert(self):

        db.session.add(self)
        db.session.commit()

    def update(self):

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()    

    def __repr__(self):
        return f'<name: {self.title}'

    def format(self):
        
        return {
            "id": self.id,
            "title": self.title,
        }

    def format2(self):

        return {
            "id": self.id,
            "title": self.title,
            "teacher_id": self.teacher_id,
            "school_year_id": self.school_year_id
        }        


class User(UserMixin, db.Model):
      id = db.Column(db.Integer, primary_key=True)
      username = db.Column(db.String(50), unique=True, nullable=False)
      password = db.Column(db.Text, nullable=False)

from form import LoginForm

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)

# class UserModel(ModelView):

#     def is_accessible(self):
#         return current_user.is_authenticated

class MyAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login_user(user)

        if current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()
    
   
    @expose('/logout/')
    def logout_view(self):
        logout_user()
        return redirect(url_for('.index'))    


admins.add_view(ViewMixin(Student, db.session))
admins.add_view(ViewMixin(Teacher, db.session))
admins.add_view(ViewMixin(Operator, db.session))
admins.add_view(ViewMixin(Assistant, db.session))    
admins.add_view(ViewMixin(Exam, db.session))
admins.add_view(ViewMixin(Question, db.session))
admins.add_view(ViewMixin(Group, db.session))
admins.add_view(ViewMixin(SchoolYear, db.session))
admins.add_view(ViewMixin(Subject, db.session))
admins.add_view(CenterView(Center, db.session))
admins.add_view(ResultView(Result, db.session))
admins.add_view(ViewMixin(ExamRoom, db.session))
admins.add_view(ViewMixin(User, db.session))

    