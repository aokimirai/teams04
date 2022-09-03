import os
import time
import cgi

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
# アプリケーションの構成
app = Flask(__name__)

# Ensure templates are auto-reloaded
# テンプレートが自動リロードされるようにする
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
# ファイルシステムを使用するようにセッションを構成します (署名付き Cookie の代わりに)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# SQLite データベースを使用するように CS50 ライブラリを構成する
db = SQL("sqlite:///map.db")

@app.route("/")
def viaa():
    return render_template("via.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/via", methods=["GET", "POST"])
def via():
    place = request.form.get("via")
    place2 = request.form.get("destination")
    means = request.form.get("means")
    print(place)
    print(place2)
    latitude = 35.1706431
    longitude = 136.8816945
    via = db.execute("SELECT * FROM place WHERE id = ?", place)
    print(via)
    via_latitude = via[0]["latitude"]
    via_longitude = via[0]["longitude"]
    destination = db.execute("SELECT * FROM place WHERE id = ?", place2)
    destination_latitude = destination[0]["latitude"]
    destination_longitude = destination[0]["longitude"]

    url = "https://www.google.com/maps/dir/?api=1&origin=名古屋駅&destination="+str(destination_latitude)+","+str(destination_longitude)+"&travelmode="+ means +"&waypoints="+str(via_latitude)+","+str(via_longitude)
    url2 = "https://maps.google.co.jp/maps?output=embed&q=名古屋駅&destination=名古屋城&travelmode=driving"
    return render_template("via.html",url=url ,url2=url2 ,a=1)

@app.route("/route")
def route():
    return render_template("route.html")