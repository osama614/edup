from flask import Blueprint, request, jsonify, abort
from .auth import guard1, CustomError
from models import *
from flask_praetorian import auth_required, roles_required, roles_accepted
import json
import random

manager = Blueprint('manager', __name__)

ENTITIES_PER_PAGE = 15


def paginate_entities(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * ENTITIES_PER_PAGE
    end = start + ENTITIES_PER_PAGE

    entities = [entity.format() for entity in selection]
    current_entities = entities[start:end]

    return current_entities

@manager.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
    
@manager.route('/login', methods=["POST"])
def login():

    req = request.get_json(force=True)
    username = req.get('username', None)
    password = req.get('password', None)
    user = guard1.authenticate(username, password)
    
    return jsonify({
        'access_token': guard1.encode_jwt_token(user)
        }), 200

@manager.route('/signup', methods=["POST"])
def signup():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        
        new_admin = Operator(username = username, password= guard1.hash_password(password))
    except (ValueError, KeyError, TypeError):
      raise CustomError({
           "message": "Bad Request",
           "description": "Check the the posted data (key_names, values_types)"
          }, 400)
    else:
        new_admin.insert()
        return f"New admin {new_admin.username} has been created!"
              
@manager.route('dashboard/all_exams')
@auth_required
@roles_required('admin')
def get_exams():

    exams = Exam.query.all()
    if len(exams) == 0:
        raise CustomError({
        "message":"Not Found",
        "description": "You should edit any exams"
    }, 404)
        
    formatted_examas = paginate_entities(request, exams)
    return jsonify({
        'exams': formatted_examas
    })

@manager.route('dashboard/exams', methods=["GET"])
def get_exam_form():
   
    try:
        subjects = Subject.query.all()
        formatted_subjects = [subject.format() for subject in subjects]

        school_years = SchoolYear.query.all()
        formatted_school_years = [school_year.format() for school_year in school_years]
        
        teachers = Teacher.query.all()
        formatted_teachers = [teacher.format2() for teacher in teachers]

        groups = Group.query.all()
        forrmatted_groups = [group.format2() for group in groups]
    except:
         raise CustomError({
           "message": "Not Found",
           "description": "Oops! there are some missing data you should have any (subjects,school_years,teachers,groups) on DB"
          }, 404)
    else:
        return jsonify({
        "subject": formatted_subjects,
        "school_years": formatted_school_years,
        "teachers": formatted_teachers,
        "groups": forrmatted_groups
    })  


@manager.route('dashboard/exams', methods=['POST'])
def create_exam():

    try:
        data = request.get_json()
        title = data['title']
        start_date = data['start_date']
        end_date = data['end_date']
        total_time = data['total_time']
        teacher_id = data['teacher_id']
        groups_ids = data['groups_ids']
        year_id = data['year_id']
        subject_id = data['subject_id']

        

        teacher = Teacher.query.get(int(teacher_id))
        year = SchoolYear.query.get(int(year_id))
        subject = Subject.query.get(int(subject_id))
        
        new_exam = Exam(title=title, start_date=start_date,end_date=end_date, total_time=total_time,
                        exam_owner=teacher, study_year=year, subject=subject)
          
            
        students = []
        
        for group_id in groups_ids:
            group_object = Group.query.get(int(group_id))
            allawable_students = group_object.students
            students += allawable_students
        
        for student in students:
            
            student.has_exam = True
            student.exams_num += 1

            new_exam.students.append(student)
            

        
    except (ValueError, KeyError, TypeError):
      raise CustomError({
           "message": "Bad Request",
           "description": "Check the the posted data (key_names, values_types)"
          }, 400)

    except:
        abort(404)  

    else:
        new_exam.insert()
        return jsonify({
            "exam_created":new_exam.title

        })  

@manager.route('dashboard/exams/<int:exam_id>', methods=["GET"])
def get_edit_examForm(exam_id):
    
    exam = Exam.query.get(int(exam_id))

    if exam == None:
        abort(404) 

    formatted_exam = exam.format()
    teacher = exam.exam_owner
    subject = exam.subject
    school_year = exam.study_year

    groups = exam.groups
    forrmatted_current_groups = [group.format() for group in groups]

    subjects = Subject.query.all()
    school_years = SchoolYear.query.all()
    teachers = Teacher.query.all()
    groups = Group.query.all()

    if len(subjects) == 0 or len(school_years) == 0 or len(teachers) == 0 or len(groups) == 0:
        
        raise CustomError({
           "message": "Not Found",
           "description": "Oops! there are some missing data you should have any (subjects,school_years,teachers,groups) on DB"
          }, 404)
 

    formatted_subjects = [subject.format() for subject in subjects]
    formatted_school_years = [school_year.format() for school_year in school_years]
    formatted_teachers = [teacher.format2() for teacher in teachers]
    
    forrmatted_groups = [group.format2() for group in groups]

    return jsonify({
        "current_exam_data": formatted_exam,
        "current_teacher" : teacher.format2(),
        "current_subject": subject.format(),
        "current_school_year": school_year.format(),
        "current_groups": forrmatted_current_groups,
        "all_groups": forrmatted_groups,
        "all_teachers": formatted_teachers,
        "all_subjects": formatted_subjects,
        "all_years": formatted_school_years
    }) 

# @manager.route('dashboard/exams/<int:exam_id>/live_exam', methods=["GET"])
# def get_edit_examForm(exam_id):

#     exam = Exam.query.get(int(exam_id))
#     if exam == None:
#         abort(404) 
#     questions = exam.questions
#     random_questions = [ random.choice()]
       


@manager.route('dashboard/exams/<int:exam_id>', methods=["PUT"])
def edit_exam(exam_id):
    try:      
        data = request.get_json()
        title = data.get('title', None)
        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)
        total_time = data.get('total_time', None)
        teacher_id = data.get('teacher_id', None)
        groups_ids = data.get('groups_ids', None)
        year_id = data.get('year_id', None)
        subject_id = data.get('subject_id', None)
        current_exam = Exam.query.get(int(exam_id))

        if teacher_id != None:
            teacher = Teacher.query.get(int(teacher_id))
            current_exam.exam_owner = teacher

        if year_id != None:
            year = SchoolYear.query.get(int(year_id))
            current_exam.study_year = year

        if subject_id != None:
            subject = Subject.query.get(int(subject_id))
            current_exam.subject = subject  

        if title != None:
            current_exam.title = title   

        if start_date != None:
            current_exam.start_date = start_date  

        if end_date != None:
            current_exam.end_date = end_date  

        if total_time != None:
            current_exam.total_time = total_time

        students = []
        if groups_ids != None:

            for group_id in groups_ids:
                group_object = Group.query.get(int(group_id))
                current_exam.groups.append(group_object)
                allawable_students = group_object.students
                students += allawable_students


            for student in students:

                student.has_exam = True
                student.exams_num += 1

                current_exam.students.append(student)

    except (ValueError, KeyError, TypeError):
        
        raise CustomError({
           "message": "Bad Request",
           "description": "Check the the posted data (key_names, values_types)"
          }, 400)

    except:
        abort(500)
    else:

        current_exam.update()

        return jsonify({
            "updated_exam": {
                "title": current_exam.title,
                "id": current_exam.id
            } 
        })    


@manager.route('dashboard/exams/<int:exam_id>', methods=["DELETE"])
def delete_exam(exam_id):

    current_exam = Exam.query.get(int(exam_id))
    current_exam.delete()

    return jsonify({
        "deleted_exam": {
            "title": current_exam.title,
            "id": current_exam.id
        }
    })    

@manager.route('dashboard/exams/<int:exam_id>/students', methods=["GET"])
def get_exam_students(exam_id):

    current_exam = Exam.query.get(int(exam_id)) 

    if current_exam == None:
        abort(404)

    exam_students = current_exam.students
    exam_teacher = current_exam.exam_owner
    exam_school_year = current_exam.study_year

    all_students = exam_teacher.students
    students_need_activation = []
    for student in all_students:
        if student.school_year_id == exam_school_year.id and student not in exam_students:
            students_need_activation.append(student)

    formatted_active_students = [student.format() for student in exam_students]
    not_active_students = [student1.format() for student1 in students_need_activation]

    return jsonify({
        "activated__students":  formatted_active_students,
        "not_active_students": not_active_students

    })

@manager.route('dashboard/exams/<int:exam_id>/students/<int:student_id>', methods=["PUT"])
def active_student(exam_id, student_id):

    current_exam = Exam.query.get(int(exam_id))
    current_student = Student.query.get(int(student_id))
    if current_exam == None or current_student == None:
        abort(404)
    current_student.exams.append(current_exam)
    current_student.has_exam = True
    current_student.exams_num += 1
    current_student.update()
    return jsonify({
        "activated_student": {
            "username": current_student.username,
            "id": current_student.id
        }
    })

@manager.route('dashboard/exams/<int:exam_id>/students/<int:student_id>', methods=["DELETE"])
def deactive_student(exam_id, student_id):
    current_student = Student.query.get(int(student_id)) 
    exam_room_user = ExamRoom.query.filter_by(exam_id=exam_id, student_id=student_id).one_or_none()
    if exam_room_user == None:
        abort(404)

    db.session.delete(exam_room_user)
    db.session.commit()
    if current_student.exams_num == 1:
        current_student.exams_num = 0
        current_student.has_exam = False
    else:
        current_student.exams_num -= 1 
    current_student.update()    
    return jsonify({
        "deactivated_student": {
            "username": current_student.username,
            "id": current_student.id
        }
    })    
    
@manager.route('dashboard/exams/<int:exam_id>/all_questions')
def get_exam_questions(exam_id):
    
    current_exam = Exam.query.get(int(exam_id))

    if current_exam == None:
        abort(404)

    questions = current_exam.questions
    formatted_questions = paginate_entities(request, questions)

    return jsonify({
        "exam_questions": formatted_questions
    })    

@manager.route('dashboard/exams/<int:exam_id>/questions')
def get_question_form(exam_id):

    
    subjects = Subject.query.all()
    school_years = SchoolYear.query.all()
    teachers = Teacher.query.all()
    if len(subjects) == 0 or len(school_years) == 0 or len(teachers) == 0:
        abort(404)

    formatted_subjects = [subject.format() for subject in subjects]
    formatted_school_years = [school_year.format() for school_year in school_years]
    formatted_teachers = [teacher.format2() for teacher in teachers]


    return jsonify({

        "subject": formatted_subjects,
        "school_years": formatted_school_years,
        "teachers": formatted_teachers
    })    

@manager.route('dashboard/exams/<int:exam_id>/questions', methods=["POST"])
def create_question(exam_id):
    try:
        data = request.get_json()
        question_head = data['question_head']
        image_url = data.get('image_url', None)
        grade = data['grade']
        correct_answer = data.get('correct_answer', None)
        answer1 = data['answer1']
        answer1_image_url = data.get('image_url', None)
        answer2 = data['answer2']
        answer2_image_url = data.get('image_url', None)
        answer3 = data['answer3'] 
        answer3_image_url = data.get('image_url', None)
        subject_id = data['subject_id']
        school_year_id = data['school_year_id']
        teacher_id = data['teacher_id']
        
        exam = Exam.query.get(int(exam_id))
        subject = Subject.query.get(int(subject_id))
        school_year = SchoolYear.query.get(int(school_year_id))
        teacher = Teacher.query.get(int(teacher_id))

        new_question = Question(question_head=question_head, image_url=image_url, grade=grade, correct_answer=correct_answer,
        answer1=answer1, answer1_image_url=answer1_image_url, answer2=answer2, answer2_image_url=answer2_image_url, answer3=answer3, answer3_image_url=answer3_image_url)
        
        new_question.subject = subject
        new_question.school_year = school_year
        new_question.question_owner = teacher
        new_question.exam = exam

    except (ValueError, KeyError, TypeError):
        raise CustomError({
           "message": "Bad Request",
           "description": "Check the the posted data (key_names, values_types)"
          }, 400)

    except:
        abort(500)
    else:

        new_question.insert()

        return jsonify({
            "question_created": {
                "text": new_question.question_head,
                "id": new_question.id 
            }
        })

@manager.route('dashboard/exams/<exam_id>/questions/<question_id>', methods=["GET"])
def edit_question_form(exam_id, question_id):

    question = Question.query.get(int(question_id))

    if question == None:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! this question is not exist"
          }, 404)
        

    formatted_question = question.format()

    teacher = question.question_owner
    subject = question.subject
    school_year = question.study_year
    
    subjects = Subject.query.all()
    school_years = SchoolYear.query.all()
    teachers = Teacher.query.all()
    
    if len(subjects) == 0 or len(school_years) == 0 or len(teachers) == 0:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! there are missing data check(teachers, school_years, subjects)"
          }, 404)

    formatted_subjects = [subject.format() for subject in subjects]
    formatted_school_years = [school_year.format() for school_year in school_years]
    formatted_teachers = [teacher.format2() for teacher in teachers]

    return jsonify({
        "current_question_data": formatted_question,
        "current_teacher" : teacher.format2(),
        "current_subject": subject.format(),
        "current_school_year": school_year.format(),
        "all_teachers": formatted_teachers,
        "all_subjects": formatted_subjects,
        "all_years": formatted_school_years

    })


@manager.route('dashboard/exams/<exam_id>/questions/<question_id>', methods=["PUT"])
def edit_question(exam_id, question_id):

    data = request.get_json()
    question_head = data.get('question_head', None)
    image_url = data.get('image_url', None)
    grade = data.get('grade', None)
    correct_answer = data.get('correct_answer', None)
    answer1 = data.get('answer1', None)
    answer1_image_url = data.get('image_url', None)
    answer2 = data.get('answer2', None)
    answer2_image_url = data.get('image_url', None)
    answer3 = data.get('answer3', None)  
    answer3_image_url = data.get('image_url', None)
    subject_id = data.get('subject_id', None)
    school_year_id = data.get('school_year_id', None)
    teacher_id = data.get('teacher_id', None)
    
    current_question = Question.query.get(int(question_id))
    if current_question == None:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! this question is not exist"
          }, 404)
    try:
        if question_head != None:
            current_question.question_head = question_head

        if image_url != None:
            current_question.image_url = image_url    

        if grade != None:
            current_question.grade = grade

        if correct_answer != None:
            current_question.correct_answer = correct_answer

        if answer1 != None:
            current_question.answer1 = answer1 

        if answer1_image_url != None:
            current_question.answer1_image_url = answer1_image_url    

        if answer2 != None:
            current_question.answer2 = answer2

        if answer2_image_url != None:
            current_question.answer2_image_url = answer2_image_url    

        if answer3 != None:
            current_question.answer3 = answer3  

        if answer3_image_url != None:
            current_question.answer3_image_url = answer3_image_url                     

        if teacher_id != None:
            teacher = Teacher.query.get(int(teacher_id))
            current_question.question_owner = teacher

        if school_year_id != None:
            year = SchoolYear.query.get(int(school_year_id))
            current_question.study_year = year

        if subject_id != None:
            subject = Subject.query.get(int(subject_id))
            current_question.subject = subject

    except (ValueError, KeyError, TypeError):
        raise CustomError({
           "message": "Bad Request",
           "description": "Check the the posted data (key_names, values_types)"
          }, 400)
    except:
        abort(500)
    else:
        current_question.update()    
        return jsonify({
            "updated_question": {
                "text": current_question.question_head,
                "id": current_question.id
            }
        })

       
@manager.route('dashboard/exams/<exam_id>/questions/<question_id>', methods=["DELETE"])
def delete_question(exam_id, question_id):

    current_question = Question.query.get(int(question_id))
    if current_question == None:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! this question is not exist"
          }, 404)

    try:
        question_data = current_question
        current_question.delete()

        return jsonify({
            "deleted_question": {
                "text": question_data.question_head,
                "id": question_data.id
            }
        })
    except:
        abort(500)

@manager.route('dashboard/all_teachers')
def get_teachers():

    teachers = Teacher.query.all()
    if len(teachers) == 0:
        raise CustomError({
           "message": "Not Found",
           "description":  "You need to edit some teachers"
          }, 404)

    formatted_teachers = paginate_entities(request, teachers)
    
    return jsonify({
        "teachers": formatted_teachers
    })

@manager.route('dashboard/teachers', methods=['GET'])
def get_teacher_form():
    
    subjects = Subject.query.all()
    if len(subjects) == 0:
        raise CustomError({
           "message": "Not Found",
           "description":  "You need to add subjects first"
          }, 404)

    formatted_subjects = [subject.format() for subject in subjects]
    
    return jsonify({
        "subjects": formatted_subjects
    })

@manager.route('dashboard/teachers', methods=['POST'])
def create_teacher():
        try:
            data = request.get_json()
            username = data['username']
            password = data['password']
            mobile = data['mobile']
            subject_id = data['subject_id']
            
            subject = Subject.query.get(int(subject_id))

            new_teacher = Teacher(username = username, password=guard1.hash_password(password), mobile= int(mobile), subject=subject) 
        except (ValueError, KeyError, TypeError):
            raise CustomError({
            "message": "Bad Request",
            "description": "Check the the posted data (key_names, values_types)"
            }, 400)

        except:
            abort(500)
        else:
            new_teacher.insert()
            return jsonify(
                {
                "created_teacher": {
                            "username": new_teacher.username,
                            "id": new_teacher.id 
                             }
               })
            

@manager.route('dashboard/teachers/<teacher_id>/groups', methods=['GET'])
def get_groups_postform(teacher_id):
    
    school_years = SchoolYear.query.all()
    if len(school_years) == 0:
        raise CustomError({
           "message": "Not Found",
           "description":  "You need to add school_years first"
          }, 404)

    formatted_school_years = [school_year.format() for school_year in school_years ]

    return jsonify({
        "school_years": formatted_school_years
    })    

@manager.route('dashboard/teachers/<teacher_id>/groups', methods=['POST'])
def create_groups(teacher_id):
    
        data = request.get_json()
        groups = data['groups']

        teacher = Teacher.query.get(int(teacher_id))
        if teacher == None:
            raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

        groups_list = []
        for group in groups:
            name = group.get('name')
            if name == None or name == "":
                raise CustomError({
                    "message": "Bad Request",
                    "description": "There is no group name attached"
                    }, 400)
            
            school_year_id = group.get('school_year_id')
            if school_year_id == None or school_year_id == "":
                raise CustomError({
                    "message": "Bad Request",
                    "description": "There is no group school_year_id attached"
                    }, 400)
            school_year = SchoolYear.query.get(int(school_year_id))
            
            new_group = Group(title=name, group_owner=teacher, study_year=school_year)
            new_group.insert()
            groups_list.append(new_group)

        created_groups = [grp.format() for grp in groups_list]


        return jsonify({
            "created_groups": created_groups
        })    

@manager.route('dashboard/teachers/<teacher_id>/groups/<int:group_id>', methods=['DELETE'])
def delete_group(teacher_id, group_id):

    current_group = Group.query.get(int(group_id))
    if current_group == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this group Id not exist"
                    }, 404)

    group_data = current_group.format()
    current_group.delete()

    return jsonify({
        "deleted_group": group_data
    })

@manager.route('dashboard/teachers/<teacher_id>/current_groups', methods=['GET'])
def update_group_form(teacher_id):

    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

    current_groups = current_teacher.groups
    school_years = SchoolYear.query.all()
    
    formatted_current_groups = [group.format2() for group in current_groups]
    formatted_school_years = [school_year.format() for school_year in school_years]
    
    
    return jsonify({
        "current_groups": formatted_current_groups,
        "all_years": formatted_school_years
    })
    
@manager.route('dashboard/teachers/<teacher_id>/current_groups', methods=['PUT'])
def update_group(teacher_id):

    data = request.get_json()
    current_updated_groups = data.get('updated_groups', None)
    new_groups = data.get('new_groups', None)

    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

    updated_groups = []
    if current_updated_groups != None:
        for group in current_updated_groups:
            if group.get('name') != None:
                old_group = Group.query.get(int(group.get('id')))
                old_group.title = group.get('name')
                
                old_group.update()
                updated_groups.append(old_group)

    created_groups = []
    if new_groups != None:
        for group in new_groups:
            name = group.get('name')
            if name == None or name == "":
                raise CustomError({
                    "message": "Bad Request",
                    "description": "There is no group name attached"
                    }, 400)

            school_year_id = group.get('school_year_id')
            school_year = SchoolYear.query.get(int(school_year_id))
            
            new_group = Group(title=name, group_owner=current_teacher, study_year=school_year)
            new_group.insert()
            created_groups.append(new_group)

    formatted_updated_groups =  [up_grp.format() for up_grp in updated_groups]  
    formatted_created_groups = [cr_grp.format() for cr_grp in created_groups]

    return jsonify({
        "updated_groups" : formatted_updated_groups,
        "created_groups" : formatted_created_groups
    })     


@manager.route('dashboard/teachers/<teacher_id>', methods=['GET'])
def update_teacher_form(teacher_id):

    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

    subject = current_teacher.subject
    subjects = Subject.query.all()
    formatted_subjects = [sbjct.format() for sbjct in subjects]

    return jsonify({
        "current_teacher_data": current_teacher.format(),
        "current_subject": subject.format(),
        "all_subjects":  formatted_subjects
    })

@manager.route('dashboard/teachers/<teacher_id>', methods=['PUT'])
def update_teacher(teacher_id):

    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)
    mobile = data.get('mobile', None)
    subject_id = data.get('subject_id', None)
    
    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)
   
    if username != None or username == "":
        current_teacher.username = username
    if password != None or password == "":
        current_teacher.password = guard1.hash_password(password)  
    if mobile != None or mobile == "":
        current_teacher.mobile = mobile
    if subject_id != None:
        subject = Subject.query.get(int(subject_id))
        current_teacher.subject = subject
    
    current_teacher.update()    


    return jsonify({
        "updated_teacher": current_teacher.format2()
    })


@manager.route('dashboard/teachers/<teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
         raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)
    teacher_data = current_teacher.format2()
    current_teacher.delete()

    
    return jsonify({
        "deleted_teacher": teacher_data
    })

@manager.route('dashboard/teachers/<teacher_id>/students')
def get_teacher_students(teacher_id):

    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

    students = current_teacher.students

    formatted_students = [student.format() for student in students]
    return jsonify({
        "teacher_students": formatted_students
    })    

@manager.route('dashboard/teachers/<teacher_id>/not_students')
def get_not_students(teacher_id):
    current_teacher = Teacher.query.get(int(teacher_id))
    if current_teacher == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

    teacher_students = current_teacher.students
    all_students = Student.query.all()

    if len(all_students) == 0:
        raise CustomError({
           "message": "Not Found",
           "description": "you don't have any students on the DB"
          }, 404)
    try:
        not_students = []
        for anystudent in all_students:
            if anystudent not in teacher_students:
                not_students.append(anystudent)
    except TypeError:
        abort(500)
       
    if len(not_students) == 0 or not_students == None:
        return "All the DB students have been added to this teacher"
        
    formatted_students = [student.format() for student in not_students]
    teacher_groups = current_teacher.groups
    school_years = SchoolYear.query.all()

    formatted_groups = [group.format2() for group in teacher_groups]
    formatted_school_years = [school_year.format() for school_year in school_years]
    
    
    return jsonify({
        "not_teacher_students": formatted_students,
        "school_years": formatted_school_years,
        "groups" : formatted_groups
    })    


@manager.route('dashboard/teachers/<int:teacher_id>/students/<int:student_id>', methods=['PUT'])
def remove_student(teacher_id, student_id):
    
    student = Student.query.get(int(student_id))
    if student == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this student Id not exist"
                    }, 404)

    should_deleted = Center.query.filter_by(teacher_id=teacher_id, student_id=student_id).first()
    db.session.delete(should_deleted)
    db.session.commit()

    return jsonify({
        "removed_student": {
            "username": student.username,
            "id": student.id
        }
    })       

@manager.route('dashboard/teachers/<int:teacher_id>/not_students/<int:student_id>', methods=['PUT'])
def add_student(teacher_id, student_id):
    data = request.get_json()
    group_id = data.get('group_id')

    current_teacher = Teacher.query.get(int(teacher_id))

    if current_teacher == None:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! this teacher is not exist"
          }, 404)

    student = Student.query.get(int(student_id))
    if student == None:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! this student is not exist"
          }, 404)

    current_teacher.students.append(student)
    group = Group.query.get(int(group_id))
    group.students.append(student)
    
    return jsonify({
        "added_student": {
            "username": student.username,
            "id": student.id
        }
    })      

@manager.route('dashboard/all_students')
def get_all_students():

    students = Student.query.all()
    if len(students) == 0:
        return {
            "Respond": "There is not any students on the DB, yet!"
        }

    formatted_students = [student.format() for student in students]

    return jsonify({
        "students": formatted_students
    })


@manager.route('dashboard/students')
def get_form_data():

    mobile_numbers = db.session.query(Student.mobile).all()
    mobiles = []
    for mobile in mobile_numbers:
        mobiles.append(mobile[0])

    school_years = SchoolYear.query.all()
    teachers = Teacher.query.all()
    groups = Group.query.all()
    
    if len(groups) == 0 or len(school_years) == 0 or len(teachers) == 0:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! there are missing data check(teachers, school_years, groups)"
          }, 404) 

    formatted_school_years = [school_year.format() for school_year in school_years]
    formatted_teachers = [teacher.format() for teacher in teachers]
    forrmatted_groups = [group.format2() for group in groups]

    return jsonify({
        "stored_mobils": mobiles,
        "school_years": formatted_school_years,
        "teachers": formatted_teachers,
        "groups": forrmatted_groups
    })

@manager.route('dashboard/students', methods=["POST"])
def post_student():
    try:

        data = request.get_json()
        fname = data['fname']
        lname = data['lname']
        username = data['username']
        password = data['password']
        mobile = data['mobile']
        school_year_id = data['school_year_id']
        teacher_id = data['teacher_id']
        group_id = data['group_id']

        group = Group.query.get(int(group_id))
        teacher = Teacher.query.get(int(teacher_id))
        school_year = SchoolYear.query.get(school_year_id)

        new_student = Student(fname=fname, lname=lname, username=username, password=guard1.hash_password(password), mobile=mobile, study_year=school_year)
        new_student.teachers.append(teacher)
        new_student.groups.append(group)

    except (ValueError, KeyError, TypeError):
        raise CustomError({
           "message": "Bad Request",
           "description": "Check the the posted data (key_names, values_types)"
          }, 400)
    
    except:
        abort(500)
    else:
        new_student.insert()

        return jsonify({
            "created_student": {
                'username': new_student.username,
                "id": new_student.id
            },
            "all_students_num": len(Student.query.all())
        })

@manager.route('dashboard/students/<int:student_id>', methods=["GET"])
def update_student_form(student_id):

    current_student = Student.query.get(int(student_id))
    if current_student == None:
        raise CustomError({
           "message": "Not Found",
           "description": "Oop! this scurrent_student is not exist"
          }, 404)

    school_year = current_student.study_year
    school_years = SchoolYear.query.all()
    formatted_school_years = [year.format() for year in school_years]


    return jsonify({
        "current_student.data": current_student.format(),
        "current_year" : school_year.format(),
        "all_years": formatted_school_years
    })


@manager.route('dashboard/students/<int:student_id>', methods=["PUT"])
def update_student(student_id):
    try:
        data = request.get_json()
        fname = data.get('fname', None)
        lname = data.get('lname', None)
        username = data.get('username', None)
        password = data.get('password', None)
        mobile = data.get('mobile', None)
        school_year_id = data.get('school_year_id', None)

        current_student = Student.query.get(int(student_id))

        if fname != None:
            current_student.fname = fname

        if lname != None:
            current_student.lname = lname

        if username != None:
            current_student.username = username    
        
        if password != None:
            current_student.password = guard1.hash_password(password)  

        if mobile != None:
            current_student.mobile = mobile 

        if school_year_id != None:
            school_year = SchoolYear.query.get(int(school_year_id)) 
            current_student.study_year = school_year
    except (ValueError, KeyError, TypeError):
            raise CustomError({
            "message": "Bad Request",
            "description": "Check the the posted data (key_names, values_types)"
            }, 400)
    except:
        abort(500)   
    else:
        current_student.update()    

        return jsonify({
            "updated_student": {
                "username": current_student.username,
                "id": current_student.id
            }
        })

@manager.route('dashboard/students/<int:student_id>', methods=["DELETE"])
def delete_student(student_id):

    current_student = Student.query.get(int(student_id))
    if current_student == None:
        raise CustomError({
                    "message": "Not Found",
                    "description":  "Oops! this teacher Id not exist"
                    }, 404)

    student_data = current_student
    current_student.delete()

    return jsonify({
        "deleted_student": {
            "username": student_data.username,
            "id": student_data.id
        }
    })


@manager.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "message": "not found resource",
        "error": 404}), 404
   

@manager.app_errorhandler(500)
def server_er(e):
    return jsonify({
        "success": False,
        "message": "internal server error",
        "error": 500}), 500  

@manager.errorhandler(CustomError)
def bad_request(e):
    return jsonify({
        "success": False,
        "message": e.error.get('message'),
        "description": e.error.get('description'),
        "status_code": e.status_code}), e.status_code
    

      