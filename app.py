import os
import re
import psycopg2
from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from psycopg2 import OperationalError
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helper import apology, get_db, login_required


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL not set")


# Source: https://realpython.com/python-sql-libraries/#postgresql
def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def query_create_insert(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def query_select(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")


db = get_db()
connection = create_connection(
    db[0]["database"], db[0]["username"], db[0]["password"], db[0]["host"], db[0]["port"])


@app.route("/", methods=["GET", "POST"])
def index():
    print(session.get("user_id"))
    if session.get("user_id") is not None:
        return render_template("dashboard.html")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        query = f"SELECT * FROM users WHERE username = '{str(request.form.get('username'))}';"
        rows = query_select(connection, query)
        # Output: [(id,username,email,hashedpassword)]
        # Example Output: [(1, 'thompson', 'itsthompson1@gmail.com', 'pbkdf2:sha256:passwordbuthashed')]

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][3], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        flash("Logged in")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("register.html")
    else:
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Those passwords didn't match.", 403)
        username = request.form.get('username')
        email = request.form.get('email')
        pass_hash = generate_password_hash(request.form.get('password'))
        regex_email = re.search(
            '^[a-zA-Z0-9.!#$%&''*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$', email)
        if not regex_email:
            return apology("Please enter an email.", 403)

        query = f"INSERT INTO users(username, email, hash) VALUES('{username}', '{email}', '{pass_hash}');"
        try:
            primary_key = query_create_insert(connection, query)
        except psycopg2.errors.UniqueViolation as e:
            return apology("This username or email is already in use!", 403)
        session["user_id"] = primary_key
    return redirect("/")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/timetable", methods=["GET", "POST"])
@login_required
def timetable():
    if request.method == "GET":
        query = f"SELECT * FROM timetable WHERE usersid = {session['user_id']}"
        timetables = query_select(connection, query)
        # Output: [(user, tableid, name, visibility, alerttime)]
        # Example Output: [(1, 1, 'test', 'public', datetime.datetime(2020, 9, 22, 2, 0, tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0, name=None)))]
        return render_template("timetable.html", timetables=timetables)
    else:
        if not request.form.get("name"):
            return apology("Please input a name for your timetable.", 403)
        else:
            name = request.form.get("name")
        if not request.form.get("visibility"):
            visibility = "public"
        else:
            visibility = request.form.get("visibility")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
