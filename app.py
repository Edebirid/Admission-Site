import os
from datetime import datetime
import click
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "CHANGE-THIS-DEV-KEY-BEFORE-DEPLOYMENT")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///school_admissions.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Enable secure cookies when deployed behind HTTPS:
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="applicant")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    application = db.relationship("AdmissionApplication", backref="applicant", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdmissionApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    pupil_full_name = db.Column(db.String(150), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(30), nullable=False)
    class_applying_for = db.Column(db.String(60), nullable=False)
    previous_school = db.Column(db.String(180))
    guardian_name = db.Column(db.String(150), nullable=False)
    guardian_phone = db.Column(db.String(40), nullable=False)
    home_address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Submitted")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class RegisterForm(FlaskForm):
    full_name = StringField("Parent/Guardian full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=160)])
    password = PasswordField("Password (at least 8 characters)", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with this email already exists.")

class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

class ApplicationForm(FlaskForm):
    pupil_full_name = StringField("Pupil's full name", validators=[DataRequired(), Length(min=2, max=150)])
    date_of_birth = DateField("Date of birth", format="%Y-%m-%d", validators=[DataRequired()])
    gender = SelectField("Gender", choices=[("", "Select"), ("Female", "Female"), ("Male", "Male"), ("Prefer not to say", "Prefer not to say")], validators=[DataRequired()])
    class_applying_for = SelectField("Class applying for", choices=[
        ("", "Select class"), ("Nursery 1", "Nursery 1"), ("Nursery 2", "Nursery 2"),
        ("Reception", "Reception"), ("Primary 1", "Primary 1"), ("Primary 2", "Primary 2"),
        ("Primary 3", "Primary 3"), ("Primary 4", "Primary 4"), ("Primary 5", "Primary 5"),
        ("Primary 6", "Primary 6"), ("JSS 1", "JSS 1"), ("JSS 2", "JSS 2"), ("JSS 3", "JSS 3")
    ], validators=[DataRequired()])
    previous_school = StringField("Previous school (if any)", validators=[Length(max=180)])
    guardian_name = StringField("Parent/Guardian name", validators=[DataRequired(), Length(min=2, max=150)])
    guardian_phone = StringField("Parent/Guardian phone", validators=[DataRequired(), Length(min=7, max=40)])
    home_address = TextAreaField("Home address", validators=[DataRequired(), Length(min=5, max=1000)])
    submit = SubmitField("Submit admission application")

class StatusForm(FlaskForm):
    status = SelectField("Application status", choices=[
        ("Submitted", "Submitted"), ("Under Review", "Under Review"),
        ("Accepted", "Accepted"), ("Waitlisted", "Waitlisted"), ("Declined", "Declined")
    ], validators=[DataRequired()])
    submit = SubmitField("Update status")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(full_name=form.full_name.data.strip(),
                    email=form.email.data.strip().lower(),
                    role="applicant")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Your account has been created. You can now complete the admission application.", "success")
        return redirect(url_for("application"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "danger")
    return render_template("login.html", form=form)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin_applications"))
    return render_template("dashboard.html", application=current_user.application)

@app.route("/application", methods=["GET", "POST"])
@login_required
def application():
    if current_user.role == "admin":
        return redirect(url_for("admin_applications"))
    existing = current_user.application
    form = ApplicationForm(obj=existing)
    if form.validate_on_submit():
        if existing is None:
            existing = AdmissionApplication(user_id=current_user.id)
            db.session.add(existing)
        form.populate_obj(existing)
        db.session.commit()
        flash("Your admission application has been saved.", "success")
        return redirect(url_for("dashboard"))
    return render_template("application.html", form=form, existing=existing)

@app.route("/admin/applications")
@login_required
def admin_applications():
    admin_required()
    applications = AdmissionApplication.query.order_by(AdmissionApplication.submitted_at.desc()).all()
    return render_template("admin_applications.html", applications=applications)

@app.route("/admin/applications/<int:application_id>", methods=["GET", "POST"])
@login_required
def review_application(application_id):
    admin_required()
    record = db.session.get(AdmissionApplication, application_id)
    if record is None:
        abort(404)
    form = StatusForm(status=record.status)
    if form.validate_on_submit():
        record.status = form.status.data
        db.session.commit()
        flash("Application status updated.", "success")
        return redirect(url_for("admin_applications"))
    return render_template("review_application.html", record=record, form=form)

@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403

@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The page you requested could not be found."), 404

@app.cli.command("init-db")
def init_db():
    """Create database tables."""
    db.create_all()
    click.echo("Database tables created.")

@app.cli.command("create-admin")
@click.option("--name", prompt="Administrator full name")
@click.option("--email", prompt="Administrator email")
@click.password_option(prompt="Administrator password", confirmation_prompt=True)
def create_admin(name, email, password):
    """Create an administrator account; never make admin access public."""
    db.create_all()
    email = email.strip().lower()
    if User.query.filter_by(email=email).first():
        click.echo("A user with that email already exists.")
        raise SystemExit(1)
    if len(password) < 12:
        click.echo("Use an administrator password of at least 12 characters.")
        raise SystemExit(1)
    user = User(full_name=name.strip(), email=email, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Administrator account created for {email}.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
