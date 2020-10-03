
from wtforms import Form, fields, validators
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

# m = generate_password_hash('admoon@#$')
# n = {"hash": m}
m = 'pbkdf2:sha256:150000$nxBiLX9z$8c7809dfc53609195ce7c9ec816126ac90acd23c26d82950be979437ce54a606'
n = check_password_hash(m,'admoon@#$')
print(n)

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



