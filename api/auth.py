from models import Teacher, Student, Operator, Assistant
from flask_praetorian import Praetorian


guard1 = Praetorian()
guard2 = Praetorian()
guard3 = Praetorian()
guard4 = Praetorian()
def setup_auth(app):
    guard1.init_app(app, Operator)
    guard2.init_app(app, Assistant)
    guard3.init_app(app, Student)
    guard4.init_app(app, Teacher)

class CustomError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code