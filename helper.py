import os
import requests
# import urllib.parse

from flask import render_template, redirect, session  # render_template, request,
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", code=code, message=escape(message)), code


def get_db():
    # postgres://YourUserName:YourPassword@YourHost:5432/YourDatabase";
    url = os.environ.get("DATABASE_URL")

    substring = url[11:]
    username = substring[:substring.find(":")]

    substring = substring[substring.find(":")+1:]
    password = substring[:substring.find("@")]

    substring = substring[substring.find("@")+1:]
    host = substring[:substring.find(":")]

    substring = substring[substring.rfind(":")+1:]
    port = substring[:substring.find("/")]

    substring = substring[substring.find("/")+1:]
    database = substring

    db = []
    db.append({"username": username, "password": password,
               "host": host, "port": port, "database": database})
    return db
