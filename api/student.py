from flask import Blueprint, request, jsonify, abort
from .auth import guard3
from models import *
from flask_praetorian import auth_required, roles_required, roles_accepted, current_user, current_user_id


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


@clint.route('<int:student_id>/teachers')
def get_teachers(student_id):

    student = Student.query.get(int(student_id))
    teachers = student.teachers

    formmated_teachers = [teacher.format() for teacher in teachers]

    return jsonify({
        "teachers": formmated_teachers
    })

@clint.route('<int:student_id>/teachers/<int:teacher_id>/results')
def get_results(student_id, teacher_id):

    results = Result.query.filter(Result.student_id == student_id, Result.teacher_id == teacher_id).all()

    formatted_results = [result.format() for result in results]


    return jsonify({
        'results': formatted_results
    })