from flask import Blueprint, request, jsonify
from .auth import guard4
from models import *
from flask_praetorian import auth_required, roles_required, roles_accepted


mentor = Blueprint('mentor', __name__)


@mentor.route('/login', methods=['POST'])
def login():

    data = request.get_json()
    password = data.get('password')
    username = data.get('username')

    user = guard4.authenticate(username, password)

    token = guard4.encode_jwt_token(user)


    return jsonify({
        'access_token': token
        }), 200

@mentor.route('/<teacher_id>/students')
def get_students(teacher_id):

    teacher = Teacher.query.get(teacher_id)
    students = teacher.students
    formatted_students = [student.format() for student in students]

    return jsonify({
        'students': formatted_students
    }) 
