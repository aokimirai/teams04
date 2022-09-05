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

        #詰まっている為、所要時間を60分,道のりを10kmと仮定して進める
        add_duration = 60
        add_distance = 10

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
