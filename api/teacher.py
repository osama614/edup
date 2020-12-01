from flask import Blueprint, request, jsonify, abort
from .auth import guard4, CustomError
from models import *
from flask_praetorian import auth_required, roles_required, roles_accepted, current_user, current_user_id
from flask_cors import CORS

mentor = Blueprint('mentor', __name__)

CORS(mentor, resources={r"*/profile/*": {"origins": "*"}})

@mentor.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

ENTITIES_PER_PAGE = 15

def paginate_entities(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * ENTITIES_PER_PAGE
    end = start + ENTITIES_PER_PAGE

    entities = [entity.format2() for entity in selection]
    current_entities = entities[start:end]

    return current_entities 

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

@mentor.route('/profile/students')
@auth_required
def get_students():
    teacher_id = current_user_id()
    teacher = Teacher.query.get(teacher_id)
    students = teacher.students
    current_students = paginate_entities(request, students)

    return jsonify({
        'students': current_students
    }) 

@mentor.route('/profile/search_students', methods=["POST"])
#@auth_required
def search_students():
    data = request.get_json()
    username = data.get('username', None)
    group_id = data.get('group_id', None)
    year_id = data.get('year_id', None)
    #teacher_id = current_user_id()
    
    if username and group_id and year_id:
        group = Group.query.get(int(group_id))
        searched_students = Student.query.filter(Student.username.ilike("%{}%".format(username)), Student.school_year_id==year_id).all()
        #current_students = paginate_entities(request, search_students)
        group_students = group.students
        requested_students = []
        for student in searched_students:
            if student in group_students:
                requested_students.append(student)
        current_students = paginate_entities(request, requested_students)
        return jsonify({
            "students": current_students
        }) 

    if username:
        searched_students = Student.query.filter(Student.username.ilike("%{}%".format(username))).all()
        current_students = paginate_entities(request, searched_students)
        return jsonify({
            "students": current_students
        })  

    if group_id:
        group = Group.query.get(int(group_id))
        group_students = group.students
        current_students = paginate_entities(request, group_students)
        return jsonify({
            "students": current_students
        })    
    if year_id:
           searched_students = Student.query.filter(Student.school_year_id==year_id).all()
           current_students = paginate_entities(request, searched_students)
           return jsonify({
                "students": current_students
            })  
    if group_id and year_id:
        searched_students = Student.query.filter(Student.school_year_id==year_id).all()
        group = Group.query.get(int(group_id))
        group_students = group.students
        requested_students = []
        for student in searched_students:
            if student in group_students:
                requested_students.append(student)
        current_students = paginate_entities(request, requested_students)
        return jsonify({
            "students": current_students
        })     

@mentor.route('/profile/students/<int:student_id>results')
@auth_required
def get_resultes(student_id):

    teacher_id = current_user_id()
    current_student = Student.query.get(int(student_id))
    if current_student == None:
        abort(404)
    student_results = Result.query.filter_by(student_id=student_id, teacher_id=teacher_id).all()
    formatted_results = [result.format() for result in student_results]
    return jsonify({
        "student_results": formatted_results,
        "student_data": current_student.format2()
    })

@mentor.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "message": "not found resource",
        "error": 404}), 404
   

@mentor.app_errorhandler(500)
def server_er(e):
    return jsonify({
        "success": False,
        "message": "internal server error",
        "error": 500}), 500  

@mentor.errorhandler(CustomError)
def bad_request(e):
    return jsonify({
        "success": False,
        "message": e.error.get('message'),
        "description": e.error.get('description'),
        "status_code": e.status_code}), e.status_code     