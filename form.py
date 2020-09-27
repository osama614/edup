
from wtforms import Form, fields, validators
#from flask_wtf import Form
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User


class LoginForm(Form):

    username = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_username(self, field):

        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
        # to compare plain text passwords use
        # if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()



