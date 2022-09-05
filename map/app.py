import os
import time
import cgi
import urllib.request, json
import urllib.parse
import datetime
import random

endpoint = 'https://maps.googleapis.com/maps/api/directions/json?'
api_key = 'APIkey'

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
def home():
    return render_template("index.html")

@app.route("/gps")
def gps():
    return render_template("gps.html")

@app.route("/via", methods=["GET", "POST"])
def via_suggest():
    url = []
    #HTMLから値を受け取る
    destination = request.form.get("destination")
    means = request.form.get("means")
    limit = request.form.get("limit")

    #目的地を選択する場合はこれを使う。
    destination = db.execute("SELECT * FROM test WHERE id = ?", destination)
    destination_latitude = destination[0]["latitude"]
    destination_longitude = destination[0]["longitude"]

    #関数を使って経由地を一つ提案
    via = suggest_via("東京駅",str(destination_latitude)+","+str(destination_longitude),means,limit)

    #GoogleMapのurlを生成してlistに追加
    i = 0
    while i != len(via):
        url.append("https://www.google.com/maps/dir/?api=1&origin=名古屋駅&destination="+str(destination_latitude)+","+str(destination_longitude)+"&travelmode="+ means +"&waypoints="+str(via[i]['latitude'])+","+str(via[i]['longitude']))
        i += 1

    return render_template("via.html" ,via=via ,url=url)







def suggest_via(origin,destination,means,limit):
    via_candidate = []

    #dbからデータを取り込む
    place_db = db.execute('SELECT * FROM test')

    #dbから読み取った値を一つずつ処理していく
    #処理はroundで移動距離、移動時間を取得して足し算、足した値が入力した値より小さければlistに格納する
    for cycle in place_db:
        print(cycle)
        route1 = route("名古屋駅",str(cycle['latitude'])+","+str(cycle['longitude']),means)
        route2 = route(str(cycle['latitude'])+","+str(cycle['longitude']),destination,means)

        #所要時間と移動距離を足し算する
        add_duration = duration_function(route1[1],route2[1])
        add_distance = distance_function(route1[0],route2[0])
        print(add_duration)
        print(add_distance)

        #もし制限時間以内に経由できるのならばlistに加える
        #場所が増えた場合は入力した時間の70%~100%のみ加える
        if int(limit) >= int(add_duration):
            temp = {'add_distance' : add_distance, 'add_duration' : add_duration}
            cycle.update(temp)
            #cycleにはid,name,latitude,longitude,add_distance,add_durationが入っている
            via_candidate.append(cycle)

    #候補を返す
    return via_candidate

    #候補に入れた経由地の候補から一つ取り出して返す
    #return random.choice(via_candidate)


# 引数で与えられた出発地点と目的地、移動手段から移動距離、移動時間を求める関数
def route(origin,destination,means):

    #現在時刻を取得
    unix_time = int(time.time())

    #デバッグ用-時間を表示
    print('=====')
    print('unixtime')
    print(unix_time)
    print('=====')

    #GoogleApiを使ってjsonファイルを取得するための文字列を生成
    nav_request = 'language=ja&origin={}&destination={}&departure_time={}&key={}&mode={}'.format(origin,destination,unix_time,api_key,means)
    nav_request = urllib.parse.quote_plus(nav_request, safe='=&')
    request = endpoint + nav_request

    #デバッグ用_取得したjsonファイルを表示
    print('')
    print('=====')
    print('url')
    print(request)
    print('=====')

    #Google Maps Platform Directions APIを実行
    response = urllib.request.urlopen(request).read()

    #結果(JSON)を取得
    directions = json.loads(response)
    print("b")

    #所要時間を取得
    for key in directions['routes']:
        #print(key) # titleのみ参照
        #print(key['legs'])
        print("a")
        for key2 in key['legs']:
            print('')
            print('=====')
            distance = key2['distance']['text']
            if means == "driving":
                #_in_trafficが付くと交通状態を加味した時間を取得できる。車で移動する時はこれを使う
                duration = key2['duration_in_traffic']['text']
                #車以外の交通状態を考えなくてよいものはこっちを使う
            else:
                duration = key2['duration']['text']
            #デバッグ用＿道のりと必要時間を表示
            print(distance)
            print(duration)
            print('=====')
    #道のりと必要時間を返す
    return distance,duration

@app.route("/login", methods=["GET", "POST"])
def login():
    #　ユーザーidをクリアする
    session.clear()
    # POSTの場合
    if request.method == "POST":
        # ユーザーネームが入力されていない
        if not request.form.get("username"):
            return apology("ユーザーネームを入力してください", 403)
        # パスワードが入力されていない
        elif not request.form.get("password"):
            return apology("パスワードを入力してください", 403)
        # 入力されたユーザーネームのデータを取得
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # ユーザーネームとパスワードが正しいか確認
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("ユーザーネームまたはパスワードが無効です", 403)
        # ユーザーを記憶する
        session["user_id"] = rows[0]["id"]
        #メッセージ
        flash("ログインしました")
        # ホームに送る
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    #　ユーザーidをクリアする
    session.clear()
    # ログインページに送る
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    # POSTの場合
    if request.method == "POST":
        # ユーザーネームが入力されていない
        if not request.form.get("username"):
            return apology("ユーザーネームを入力してください", 400)
        # ユーザーネームが既に使われている
        if len(db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))) != 0:
            return apology("このユーザーネームは既に使われています", 400)
        # パスワードが入力されていない
        elif not request.form.get("password"):
            return apology("パスワードを入力してください", 400)
        # パスワードが一致しない
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("パスワードが一致しません", 400)
        # データベースに入れる
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))
        #メッセージ
        flash("登録が完了しました")
        # ログインページに送る
        return redirect("/login")
    else:
        return render_template("register.html")


#合計時間を計算する関数です
def duration_function(time1,time2):
    time = [time1,time2]
    i,n,x,y,xx,yy = 0,0,0,0,0,0
    hour,day,minutes = 0,0,0
    while i != 2:
        while n != len(time[i]):
            if time[i][n] == "日":
                #　日　が出てくるまでの数字を文字型から整数型に変換して変数に代入
                day += int(time[i][0:n])
                x = 1
                xx = n+1
            if time[i][n] == "時":
                #　日　以降で　時間　が出てくるまでの数字を文字型から整数型に変換して変数に代入
                hour += int(time[i][xx:n])
                y = 1
                yy = n+2
            if time[i][n] == "分":
                #　時間　以降で　分　が出てくるまでの数字を文字型から整数型に変換して変数に代入
                minutes += int(time[i][yy:n])
            n += 1
        i += 1
        x,y,n,xx,yy = 0,0,0,0,0

    minutes += ((day * 24) + hour) * 60
    print(minutes)
    #if minutes >= 60:
        #hour += minutes // 60
        #minutes = minutes % 60
    #if hour >= 24:
        #day += hour // 24
        #hour = hour % 24
        # print(str(day)+'日'+str(hour)+'時間'+str(minutes)+'分')

    return minutes

#合計距離を計算する関数
def distance_function(distance1,distance2):
    distance = [distance1,distance2]
    add_distance = 0
    i,n,k = 0,0,0


    #なぜか i!=2 にするとエラーが出ます。
    while i != 1:
        while n != len(distance[i]):
            if distance[i][n] == "k":
                #数字と単位(km)を分割してmへ変換。1.1のように小数点で出てくる可能性があるのでfloatにしてみました。
                add_distance += float(distance[i].split('km')[0])*1000
                k = 1
            n += 1
        if k == 0:
            add_distance += float(distance[i].split("m")[0])
        i += 1

    return add_distance
