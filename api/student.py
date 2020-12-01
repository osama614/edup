from flask import Blueprint, request, jsonify, abort
from .auth import guard3
from models import *
from flask_praetorian import auth_required, roles_required, roles_accepted, current_user, current_user_id
from .auth import CustomError
from random import shuffle 
from datetime import datetime
from flask_cors import CORS

clint = Blueprint('clint', __name__)
CORS(clint, resources={r"/profile/*": {"origins": "*"}})

# @clint.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     return response

@clint.route('/login', methods=["POST"])
def login():

    req = request.get_json(force=True)
    username = req.get('username', None)
    password = req.get('password', None)
    user = guard3.authenticate(username, password)
    
    return jsonify({
        'access_token': guard3.encode_jwt_token(user)
        }
        ), 200


@clint.route('profile/teachers')
@auth_required
def get_teachers():
    
    student_id = current_user_id()
    student = Student.query.get(int(student_id))
    teachers = student.teachers
    active_exams = student.exams
    formatted_exams = []
    if len(active_exams) != 0:
        formatted_exams += [exam.format3() for exam in active_exams]

    if len(teachers) == 0:
        raise CustomError({
        "message":"Not Found",
        "description": "This student dosn't have any teachers!"
    }, 404)

    formmated_teachers = [teacher.format() for teacher in teachers]
    return jsonify({

        "current_student": student.format(),
        "student_teachers": formmated_teachers,
        "active_exams": formatted_exams
    })

@clint.route('profile/exams/<int:exam_id>')
@auth_required
def get_exams(exam_id):
    exam = Exam.query.get(int(exam_id))
    if exam == None:
        abort(404)

    num = len(exam.questions)

    formatted_exam = exam.format()
    return jsonify({
        "exam_data": formatted_exam,
        "num_questions": num
    })
@clint.route('profile/teachers/<int:teacher_id>/results')
@auth_required
def get_results(teacher_id):

    student_id = current_user_id()
    results = Result.query.filter(Result.student_id == student_id, Result.teacher_id == teacher_id).all()
    formatted_results = [result.format() for result in results]
    return jsonify({

        'results': formatted_results
    })

    
@clint.route('profile/teachers/<int:exam_id>/examroom')
@auth_required
def get_questions(exam_id):
    
    current_exam = Exam.query.get(int(exam_id))

    if current_exam == None:
        abort(404)

    if current_exam.start_date > datetime.now():
        return f"The will start in {current_exam.start_date - datetime.now()}" 
    
    exam_data = current_exam.format2()
    teacher = current_exam.exam_owner.username
    questions = current_exam.questions
    subject = current_exam.subject.name
    formatted_questons = [question.format() for question in questions]
    shuffle(formatted_questons)
    
    return jsonify(
        {
        "teacher": teacher,
        "subject": subject,
        "exam_data": exam_data,
        "questions": formatted_questons
    }
    )
@clint.route('profile/teachers/<int:exam_id>/examroom', methods=["POST"])
@auth_required
def submit_exam(exam_id):

    data = request.get_json()
    grade = data.get('grade')
    student_id = current_user_id()

    current_exam = Exam.query.get(int(exam_id))
    if current_exam == None:
        abort(404)

    teacher = current_exam.exam_owner
    current_student = Student.query.get(int(student_id)) 

    result = Result.query.filter_by(exam_id=exam_id, student_id=student_id).one_or_none()
    if result == None:
        abort(404)

    result.title = current_exam.title
    result.start_date = current_exam.start_date
    result.student_grade = grade
    result.total_grade = current_exam.total_grade
    result.teacher = teacher
    result.update()

    room = ExamRoom.query.filter_by(student_id=student_id, exam_id=exam_id).one_or_none()
    room.delete()
    if current_student.exams_num == 1:
        current_student.exams_num = 0
        current_student.has_exam = False
    else:
        current_student.exams_num -= 1
    current_student.update()         

    
    return 'Your data has been submited successfully!'

@clint.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "message": "not found resource",
        "error": 404}), 404
   

@clint.app_errorhandler(500)
def server_er(e):
    return jsonify({
        "success": False,
        "message": "internal server error",
        "error": 500}), 500  

@clint.errorhandler(CustomError)
def bad_request(e):
    return jsonify({
        "success": False,
        "message": e.error.get('message'),
        "description": e.error.get('description'),
        "status_code": e.status_code}), e.status_code   
    
    
    

