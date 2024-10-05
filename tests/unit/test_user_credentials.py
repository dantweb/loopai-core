from werkzeug.security import generate_password_hash

from loopai_src.web import User, db

new_user = User(
    name='user777',
    login='user777',
    password=generate_password_hash('allahuakhbar'),  # bcrypt hash

)

db.session.add(new_user)
db.session.commit()
