from flask import Flask, render_template, request, redirect, session, url_for, make_response, flash, get_flashed_messages
import jwt
from datetime import datetime, timedelta
from functools import wraps
import re


from models import User, db




app = Flask(__name__)
app.config["SECRET_KEY"]="d951bdc9bb58409d"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)






def is_valid_password(password):
    if len(password) < 8:
        return "Password: minimum 8 characters"
    if not re.search(r"[A-Z]",password):
        return "Password: at least 1 uppercase"
    if not re.search(r"[a-z]",password):
        return "Password: at least 1 lowercase"
    if not re.search(r"[0-9]",password):
        return "Password: at least 1 number"
    if not re.search(r"[!@#$%^&*(),.?\":_{}|<->]",password):
        return "Password: at least 1 special char  (!@#$%^&*()\"-_|?,.<>)"

    return None








def token_required(f):
    @wraps(f)
    def decorated():
        token = request.cookies.get('jwt_token')

        if not token:
            return render_template('index.html')

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = data['username']
        
        except:
            flash('Something went wrong')
            return redirect(url_for("home"))

        return f(current_user)
    return decorated










@app.route('/')
@token_required
def home(current_user):

    return redirect(url_for("dashboard"))
    
 


@app.route('/login', methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        
        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow()+timedelta(minutes=30),
        }, app.config["SECRET_KEY"], algorithm="HS256")

        resp = make_response(render_template("dashboard.html", username=username))
        resp.set_cookie('jwt_token', token, httponly=True, secure=False)
        
        return  resp
        
        
    else:
        flash("Incorrect username or password")
        return redirect(url_for("home"))
        

@app.route('/register', methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    pass_type_error = is_valid_password(password)
    if user:
        err=["User already here!", "Change your username"]
        for err in err:
            flash(err)
        return redirect(url_for("home"))
        
    
    elif pass_type_error:
        flash(pass_type_error)
        return redirect(url_for("home"))

    else:
        new_user = User(username=username)
        new_user.set_password(password)
        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow()+timedelta(minutes=30),
        }, app.config["SECRET_KEY"], algorithm="HS256")

        resp = make_response(redirect(url_for("dashboard")))
        resp.set_cookie('jwt_token', token, httponly=True, secure=False)
        db.session.add(new_user)
        db.session.commit()
        return  resp

   



@app.route('/dashboard')
@token_required
def dashboard(current_user):
    return render_template("dashboard.html", username=current_user)

   






@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for("home")))
    resp.set_cookie('jwt_token', '', expires=0)
    return resp







if __name__ =="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)    

