from flask import *

from flask_mysqldb import MySQL


app=Flask(__name__)


app.secret_key="smartcivic"

import os
from werkzeug.utils import secure_filename




app.config["MYSQL_HOST"]="localhost"

app.config["MYSQL_USER"]="root"

app.config["MYSQL_PASSWORD"]="preeti@123"

app.config["MYSQL_DB"]="smart_civic_connect"


mysql=MySQL(app)

app.config["MYSQL_DB"] = "smart_civic_connect"

app.config["UPLOAD_FOLDER"] = "static/profile_photos"



@app.route("/")
def home():

    return render_template(
        "index.html"
    )



@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return redirect("/admin_dashboard")

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM complaints"
    )

    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Pending'"
    )

    pending = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Resolved'"
    )

    resolved = cur.fetchone()[0]

    cur.close()

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        resolved=resolved
    )




@app.route("/report", methods=["GET","POST"])
def report():

    if "user" not in session:
        return redirect("/login")

    if request.method=="POST":

        title=request.form["title"]

        category=request.form["category"]

        description=request.form["description"]

        cur=mysql.connection.cursor()

        cur.execute("""

        INSERT INTO complaints(

        title,
        category,
        description,
        status

        )

        VALUES(

        %s,
        %s,
        %s,
        'Pending'

        )

        """,

        (
        title,
        category,
        description
        ))

        mysql.connection.commit()

        cur.close()

        return redirect("/dashboard")

    return render_template(
        "report_issue.html"
    )


@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect("/login")

    if session["role"]!="admin":
        return redirect("/dashboard")

    cur=mysql.connection.cursor()

    cur.execute("""

    SELECT *

    FROM complaints

    ORDER BY id DESC

    """)

    complaints=cur.fetchall()

    cur.close()

    return render_template(
        "admin.html",
        complaints=complaints
    )

@app.route(
"/update_status",
methods=["POST"]
)

def update_status():

    if "user" not in session:
        return redirect("/login")

    if session["role"]!="admin":
        return redirect("/dashboard")

    complaint_id=request.form["id"]

    status=request.form["status"]

    cur=mysql.connection.cursor()

    cur.execute("""

    UPDATE complaints

    SET status=%s

    WHERE id=%s

    """,

    (
    status,
    complaint_id
    ))

    mysql.connection.commit()

    cur.close()

    return redirect(
        "/admin"
    )

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method=="POST":

        name=request.form["name"]
        email=request.form["email"]
        password=request.form["password"]

        cur=mysql.connection.cursor()

        cur.execute("""
        INSERT INTO users(
        name,
        email,
        password,
        role
        )

        VALUES(
        %s,
        %s,
        %s,
        %s
        )
        """,

        (
        name,
        email,
        password,
        "user"
        ))

        mysql.connection.commit()

        cur.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT *
            FROM users
            WHERE email=%s
            AND password=%s
        """, (email, password))

        user = cur.fetchone()

        cur.close()

        if user:

            session["user"] = user[2]     # email
            session["role"] = user[4]     # role

            if session["role"] == "admin":
                return redirect("/admin_dashboard")

            return redirect("/dashboard")

        return "Invalid Email or Password"

    return render_template("login.html")


@app.route("/admin_dashboard")
def admin_dashboard():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM complaints")

    complaints = cur.fetchall()

    cur.close()

    return render_template(
        "admin.html",
        complaints=complaints
    )

@app.route("/profile", methods=["GET","POST"])
def profile():

    if "user" not in session:
        return redirect("/login")

    cur=mysql.connection.cursor()

    if request.method=="POST":

        name=request.form["name"]
        email=request.form["email"]
        phone=request.form["phone"]
        address=request.form["address"]

        file=request.files.get("photo")

        filename=None

        if file and file.filename!="":

            filename=secure_filename(file.filename)

            file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        if filename:

            cur.execute("""
            UPDATE users

            SET
            name=%s,
            email=%s,
            phone=%s,
            address=%s,
            photo=%s

            WHERE email=%s
            """,

            (
            name,
            email,
            phone,
            address,
            filename,
            session["user"]
            ))

        else:

            cur.execute("""
            UPDATE users

            SET
            name=%s,
            email=%s,
            phone=%s,
            address=%s

            WHERE email=%s
            """,

            (
            name,
            email,
            phone,
            address,
            session["user"]
            ))

        mysql.connection.commit()

        session["user"]=email

    cur.execute("""
    SELECT
    name,
    email,
    phone,
    address,
    photo

    FROM users

    WHERE email=%s
    """,

    (
    session["user"],
    ))

    user=cur.fetchone()

    cur.close()

    return render_template(
        "profile.html",
        user=user
    )


@app.route("/track", methods=["GET","POST"])
def track():

    if "user" not in session:
        return redirect("/login")

    result=None

    if request.method=="POST":

        complaint_id=request.form["id"]

        cur=mysql.connection.cursor()

        cur.execute("""

        SELECT
        id,
        title,
        category,
        description,
        status

        FROM complaints

        WHERE id=%s

        """,

        (
        complaint_id,
        ))

        result=cur.fetchone()

        cur.close()

    return render_template(
        "track_issue.html",
        result=result
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

if __name__=="__main__":

    app.run(
        debug=True
    )
