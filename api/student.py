from flask import Blueprint, request, jsonify, abort
from .auth import guard3
from models import *
from flask_praetorian import auth_required, roles_required, roles_accepted, current_user, current_user_id
from .auth import CustomError
import random

clint = Blueprint('clint', __name__)

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
def get_teachers():
    
    student_id = current_user_id()
    student = Student.query.get(int(student_id))
    teachers = student.teachers
    active_exams = student.exams
    formatted_exams = []
    if len(active_exams) != 0:
        formatted_exams += [exam.format() for exam in active_exams]

    if len(teachers) == 0:
        raise CustomError({
        "message":"Not Found",
        "description": "This student dosn't have any teachers!"
    }, 404)

    formmated_teachers = [teacher.format() for teacher in teachers]
    return jsonify({

        "student": student.format(),
        "teachers": formmated_teachers,
        "exams": formatted_exams
    })

@clint.route('profile/exams/<int:exam_id>')
def get_exams(exam_id):
    exam = Exam.query.get(int(exam_id))
    if exam == None:
        abort(404)
    formatted_exam = exam.format()
    return jsonify({
        "exam_data": formatted_exam
    })
@clint.route('profile/teachers/<int:teacher_id>/results')
def get_results(teacher_id):

    student_id = current_user_id()
    results = Result.query.filter(Result.student_id == student_id, Result.teacher_id == teacher_id).all()
    formatted_results = [result.format() for result in results]
    return jsonify({

        'results': formatted_results
    })

    
@clint.route('profile/teachers/<int:exam_id>/examroom')
def get_questions(exam_id):

    current_exam = Exam.query.get(int(exam_id))
    teacher = current_exam.exam_owner
    questions = current_exam.questions
    formatted_questons = [question.format() for question in questions]
    random.shuffle(formatted_questons)
    
    return jsonify(
        {
        "teacher": teacher.username,
        "subject": current_exam.subject.name,
        "exam_data": {
            "title": current_exam.title,
            'total_time': current_exam.total_time
        },
        "questions": formatted_questons
    }
    )