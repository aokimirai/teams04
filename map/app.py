import os
import time
import cgi
import urllib.request, json
import urllib.parse
import datetime
import random
import sys
import requests
import googlemaps
import io

endpoint = 'https://maps.googleapis.com/maps/api/directions/json?'
api_key = 'AIzaSyAXJI-ZznTxw_cMvR8iiYQXV7O_o4H6lHs'

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
def gps():
    if request.method == "POST":
        lat = request.form['lat']
        long = request.form['long']
        print("緯度",lat)
        return render_template("index.html")
    else:
        return render_template("index.html")

#ポイントカードの処理
@app.route("/point", methods=["GET","POST"])
def point():
    #テスト段階はuseridは1とする
    userid = 1
    if request.method == "POST":
        keyword = request.form.get("keyword")
        print(keyword)
        #データベースにあるキーワード分だけ回す
        a = db.execute(("SELECT * FROM test_point"))
        for cycle in a:
            if cycle['string'] == keyword:
                #もしキーワードがあっていれば、1ポイント追加する
                points = db.execute("SELECT * FROM test_point_user WHERE id = ?", userid)[0]['point']
                db.execute("UPDATE test_point_user SET point=? WHERE id=?",points+1 ,userid)
                db.execute("DELETE FROM test_point WHERE string=?", keyword)
                print("point取得")
                break
    #ポイント数を返す
    return render_template("point.html",point = db.execute("SELECT * FROM test_point_user WHERE id = ?", userid)[0]['point'])

#ポイントカード（店舗用）の処理、キーワードを生成してデータベースに保存
@app.route("/point_store",methods=["GET","POST"])
def point_store():
    keyword=""
    if request.method == "POST":
        #一文字ずつ文字をランダムに生成して変数に追加する
        i = 0
        while i != 5:
            keyword = keyword + chr(random.randint(97, 123))
            i += 1
        #生成したキーワードをデータベースに保存する
        db.execute("INSERT INTO test_point (string) VALUES ( ? )",keyword)
    return render_template("point_store.html",keyword=keyword)


@app.route("/via", methods=["GET", "POST"])
def via_suggest():
    if request.method == "POST":
        url = []
        #HTMLから値を受け取る
        means = request.form.get("means")
        limit = request.form.get("limit")
        print(limit.isdigit())

        if limit.isnumeric() == False:
            return apology("所要時間を入力してください。", 400)
        if not request.form.get("origin"):
            return apology("出発地点を入力してください。",400)
        if not request.form.get("destination"):
            return apology("目的地を入力してください。",400)

        origin = request.form.get("origin")
        destination = request.form.get("destination")
        keyword = request.form.get("keyword")

        #関数を使って施設名から住所を取得
        destination_cie = get_address(destination)
        if destination_cie == False:
            return apology("住所が見つかりませんでした。",501)
        origin_cie = get_address(origin)
        if destination_cie == False:
            return apology("住所が見つかりませんでした。",501)
        #関数をつかって経由地を検索数字は東京駅の座標
        suggest_place = search_place(origin_cie[0],origin_cie[1],destination_cie[0],destination_cie[1],means,limit,keyword)

        #目的地を選択する場合はこれを使う。
        #データベースから目的地の緯度経度を取得
        """
        destination = db.execute("SELECT * FROM test WHERE id = ?", destination)
        destination_latitude = destination[0]["latitude"]
        destination_longitude = destination[0]["longitude"]
        """


        #関数を使って経由地を提案
        via = suggest_via(origin,str(destination_cie[0])+","+str(destination_cie[1]),suggest_place,means,limit)

        #GoogleMapのurlを生成してlistに追加
        i = 0
        while i != len(via):
            url.append("https://www.google.com/maps/dir/?api=1&origin="+str(origin_cie[0])+","+str(origin_cie[1])+"&destination="+str(destination_cie[0])+","+str(destination_cie[1])+"&travelmode="+ means +"&waypoints="+str(via[i]['lat'])+","+str(via[i]['lng']))
            i += 1
        print(url)
        return render_template("via.html" ,via=via ,url=url)
    else:
        return apology("未実装です。",500)


#経由地候補を返す関数です。
def suggest_via(origin,destination,place,means,limit):
    via_candidate = []
    via_temp = ""
    # | で区切られた場所を文字列で生成
    for cycle in place:
        via_temp += "|" + str(cycle['lat']) + "," + str(cycle['lng'])
    #先頭の | を削除する
    via_temp = via_temp[1:]

    #関数を使って所要時間と道のりを取得
    route1 = route(origin,via_temp,means)
    route2 = route(via_temp,destination,means)

    i = 0
    #経由地検索してlistに格納した数だけ回す
    for cycle in place:
        #先ほど関数を使い所有時間と道のりを取得した関数から時間と距離を別の関数に入れる
        add_distance = route1['rows'][0]['elements'][i]['distance']['value'] + route2['rows'][i]['elements'][0]['distance']['value']
        add_duration = route1['rows'][0]['elements'][i]['duration']['value'] + route2['rows'][i]['elements'][0]['duration']['value']

        #移動手段が車の時は交通情報を加味した時間を入れる
        if means == "driving":
            add_duration = route1['rows'][0]['elements'][i]['duration_in_traffic']['value'] + route2['rows'][i]['elements'][0]['duration_in_traffic']['value']
        #もし取得した時間が入力値以下なら経由地候補に入れる
        #取得した時間は秒のため、入力値も秒に直す
        if add_duration <= int(limit) * 60:
            temp = unit(add_distance,add_duration//60)
            temp = {'add_distance' : temp[0], 'add_duration' : temp[1]}
            #辞書式として距離、所要時間を追加
            cycle.update(temp)
            #cycleにはname,latitude,longitude,add_distance,add_durationが入っている
            via_candidate.append(cycle)
        i += 1
    #経由地候補を返す
    return via_candidate

    #候補に入れた経由地の候補から一つ取り出して返す
    #return random.choice(via_candidate)

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

#経由地候補を返す関数です。
def suggest_via(origin,destination,place,means,limit):
    via_candidate = []
    via_temp = ""
    # | で区切られた場所を文字列で生成
    for cycle in place:
        via_temp += "|" + str(cycle['lat']) + "," + str(cycle['lng'])
    #先頭の | を削除する
    via_temp = via_temp[1:]

    #関数を使って所要時間と道のりを取得
    route1 = route(origin,via_temp,means)
    route2 = route(via_temp,destination,means)

    i = 0
    #経由地検索してlistに格納した数だけ回す
    for cycle in place:
        #先ほど関数を使い所有時間と道のりを取得した関数から時間と距離を別の関数に入れる
        add_distance = route1['rows'][0]['elements'][i]['distance']['value'] + route2['rows'][i]['elements'][0]['distance']['value']
        add_duration = route1['rows'][0]['elements'][i]['duration']['value'] + route2['rows'][i]['elements'][0]['duration']['value']

        #移動手段が車の時は交通情報を加味した時間を入れる
        if means == "driving":
            add_duration = route1['rows'][0]['elements'][i]['duration_in_traffic']['value'] + route2['rows'][i]['elements'][0]['duration_in_traffic']['value']
        #もし取得した時間が入力値以下なら経由地候補に入れる
        #取得した時間は秒のため、入力値も秒に直す
        if add_duration <= int(limit) * 60:
            temp = unit(add_distance,add_duration//60)
            temp = {'add_distance' : temp[0], 'add_duration' : temp[1]}
            #辞書式として距離、所要時間を追加
            cycle.update(temp)
            #cycleにはname,latitude,longitude,add_distance,add_durationが入っている
            via_candidate.append(cycle)
        i += 1
    #経由地候補を返す
    return via_candidate

#単位を整える関数です。
def unit(distance,duration):
    #変数定義
    km,day,hour = 0,0,0
    min = duration
    m = distance
    add_distance = ""
    add_duration = ""

    #もし1000m以上ならば
    if distance >= 1000:
        #kmに単位変換し、表に表示する単位をkmにする。
        km = distance / 1000
        add_distance = str(km) + "km"
        #1000m以下ならmで表示
    else:
        add_distance += str(m) + "m"

    #もし60分以上ならば
    if duration >= 60:
        #時　に単位変換する。余りは分で表示
        hour = duration // 60
        min = duration % 60
        #もし24時間以上ならば　日　に単位変換する。余りは時で表示
        if hour >= 24:
            day = hour // 24
            hour = hour % 24
            add_duration = str(day) + "日"
        if min != 0:
            add_duration += str(hour) + "時間"
    add_duration += str(min) + "分"

    return(add_distance,add_duration)

#施設名から緯度経度に変換する関数
def get_address(place):
    #geocodeAPIのURL
    Url = "https://maps.googleapis.com/maps/api/geocode/json"

    #パラメータの設定
    params={}
    params["key"] = api_key #取得したAPIキーをセット
    params["address"] = place
    params["language"] = "ja"

    #リクエスト結果
    answer = requests.get(Url, params).json()

    #なぜか上手くいかない...
    if answer['status'] == 'ZERO_RESULTS':
        return False

    #取得したデータから緯度経度を抽出し、　緯度,経度　の形にして変数に保存する
    #address = str(answer['results'][0]['geometry']['location']['lat']) + "," + str(answer['results'][0]['geometry']['location']['lng'])
    return answer['results'][0]['geometry']['location']['lat'],answer['results'][0]['geometry']['location']['lng']

def search_place(original_latitude,original_longitude,destination_latitude,destination_longitude,means,limit,keyword):
    client = googlemaps.Client(api_key) #インスタンス生成
    #loc = {'lat': 35.6288505, 'lng': 139.65863579999996} # 軽度・緯度を取り出す

    #目的地とスタート地点の中心を起点とする
    loc = {'lat': str((float(original_latitude) + destination_latitude)/2), 'lng': str((original_longitude + destination_longitude)/2)}
    #それぞれの手段によって半径を変える
    if means == 'driving':
        radius = 333 * int(limit)
    if means == 'bicycling':
        radius = 166 * int(limit)
    if means == 'walking':
        radius = 66 * int(limit)
    #placesAPIで検索する際の最大の半径は50kmなので50kmまでに統一する
    if radius > 500000:
        radius = 500000
    print(loc)
    print(radius)

    #結果を表示
    place_results = client.places_nearby(location=loc, radius=radius ,keyword=keyword ,language='ja')
    print(place_results)
    results = []
    suggest_place = []
    for place_result in place_results['results']:
        results.append(place_result)

    #print(random.choice(results)['geometry']['location'])
    #print(random.choice(results)['name'])

    i = 0
    while i != 3:
        temp = random.choice(results)
        temp1 = temp['geometry']['location']
        temp2 = {'name':temp['name']}
        temp1.update(temp2)
        suggest_place.append(temp1)
        i += 1

    #print(random.choice(results))
    print(suggest_place)
    return suggest_place

#distance matrix apiで距離・時間を取得する関数
def route(origin,destination,means):
    api = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    #リクエストするためのパラメーターを設定
    params = {
        'key': api_key,
        'mode': means,
        'departure_time': 'now',
        'origins': origin,
        'destinations': destination,
        'language': "ja"
    }

    #APIにリクエストして結果を受け取る
    raw_response = requests.get(api, params)
    #JSONファイルをデコードしてプログラムが読める形に変形する
    parsed_response = json.loads(raw_response.text)

    #取得したデータを返す
    return parsed_response

@app.route("/mypage")
def mypage():
    return render_template("mypage.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/favorite")
def favorite():
    return render_template("favorite.html")
