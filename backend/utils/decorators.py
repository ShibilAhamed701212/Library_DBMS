from functools import wraps
from flask import session, redirect


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper


def member_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "member":
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper
