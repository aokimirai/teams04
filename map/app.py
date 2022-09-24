import os
import cgi
import urllib.request, json
import urllib.parse
import datetime as dt
import random
import sys
import requests
import googlemaps
import io
import werkzeug
import time
from datetime import datetime
import schedule
import sqlite3
import re
import json
import ast
import math


endpoint = 'https://maps.googleapis.com/maps/api/directions/json?'
#################################################################################################
#APIキーを別ファイルから取り出すプログラム
#キーのほうで使用上限を設けていますが、外部にAPIキーが漏れないように作りました。
#################################################################################################
with open("APIkey.txt") as f:
    APIkey = f.read()
    print(APIkey)
api_key = APIkey

# 毎日12:00にキーワードを変更する
def clear():
    con = sqlite3.connect('./map.db')
    db = con.cursor()
    db.execute("SELECT REPLACE(keycount,'1','0') FROM tenantkeys")
    con.commit()
    con.close()
schedule.every().day.at("00:00").do(clear)

api_value = 1
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

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

# 画像保存用
UPLOAD_POST_FOLDER = './static/upload'
ALLOWED_EXTENSIONS = set(['.jpg','.gif','.png','image/gif','image/jpeg','image/png'])
app.config['UPLOAD_FOLDER'] = UPLOAD_POST_FOLDER

# Configure CS50 Library to use SQLite database
# SQLite データベースを使用するように CS50 ライブラリを構成する
db = SQL("sqlite:///map.db")



#################################################################################################
#ホームページ
#緯度経度を取得できればその地点を、できなければ東京駅を地点にしたページを表示する
#placeは周辺地点の場所(車で60分以内に行ける場所)
#geoはHTMLの　現在地から出発するボタン　と　出発地点のフォーム　の表示切り替えに使う
#################################################################################################
@app.route("/",methods=["GET", "POST"])
def gps():
        if request.method == "POST":


            #####################################
            #住所バレ防止のため、現在地を取得機能をコメントアウトしています。(DEMODAY用)
            #住所を取得したい場合は下の値を使ってください
            #####################################
            #lat = request.form['lat']
            #long = request.form['long']

            #####################################
            #DEMODAY用。京都駅の座標をセットしています。
            #現在地を取得したい場合は削除してください
            #####################################
            lat = 35.0036559
            long = 135.7785534


            keyword = ""
            geo = 1
            place = search_place(lat,long,lat,long,"driving",60,keyword,60)
            return render_template("index.html",lat=lat ,long=long ,place=place ,key=api_key ,geo=geo)
        try:
            if session["tenant_user_id"]:
                return redirect("/tenanthome")
        except KeyError:
            latitude = 	35.6809591
            longitude = 139.7673068
            keyword = ""
            geo = 0
            place = search_place(latitude,longitude,latitude,longitude,"driving",60,keyword,60)
            return render_template("index.html",place = place,key = api_key ,lat=latitude ,long=longitude ,geo=geo)


#################################################################################################
#ポイントカードの処理
#データベースに保存されたキーワードがあればポイントを加算する
#################################################################################################
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


#################################################################################################
#ポイントカードの処理
#ボタンを押したらランダムな文字列を生成してデータベースに保存する
#################################################################################################
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


#################################################################################################
#ランキングを処理
#配列にuseridの順に値を入れていって、最終的に辞書式の中に名前と値を入れるようにする
#[useridが1の人の値,useridが2の人の値,useridが3の人の値]（forループで加算していく)
#配列に人数分0を代入して辞書式に
#その値を使って辞書式に {名前:スコア} といった感じに保存(forループで)
#作った辞書式を移動手段とともに辞書式として保存{driving:{name1:2,name2:2,name3,3},walking:{name1:2,name2:2,name3,3}}といった感じ
#################################################################################################
@app.route("/ranking", methods=["GET", "POST"])
def ranking():
    if request.method == "POST":
        means = request.form.get('means')
    #デバッグ用
    else:
        means = "driving"
    #辞書式で値を保存(listの中身は左からuseridが1の人、2の人,3の人...といった具合)
    score = {"walking": [], "bicycling": [], "driving": []}
    user_data = db.execute("SELECT * FROM users")
    name = []
    #ユーザー数だけlistに0を入れる
    for cycle in user_data:
        score["walking"].append(0)
        score["bicycling"].append(0)
        score["driving"].append(0)
        name.append(cycle['username'])
    temp = db.execute("SELECT * FROM history")
    #辞書式のやつに値を保存
    for cycle in temp:
        score[cycle["way"]][cycle["userid"] - 1] += float(cycle["distance"])


    driving_score = {}
    bicycling_score = {}
    walking_score = {}
    r = 0
    for temp_name in name:
        driving_score.update({temp_name:score["driving"][r]})
        bicycling_score.update({temp_name:score["bicycling"][r]})
        walking_score.update({temp_name:score["walking"][r]})
        r += 1
    print(driving_score)
    #score = {'driving':2,'walking':3,'bicycling':4}
    score = {"walking": sorted(walking_score.items() ,key=lambda x:x[1], reverse=True), "bicycling": sorted(bicycling_score.items() ,key=lambda x:x[1], reverse=True), "driving": sorted(driving_score.items() ,key=lambda x:x[1], reverse=True)}
    print(score)
    """
    score['walking'] = dic.update(score['walking'])
    score['bicycling'] = dic.update(score['bicycling'])
    score['driving'] = dic.update(score['driving'])
    print(score)
    """
    print(user_data)

    #辞書式で保存した値とユーザー名、移動手段を返す
    return render_template("ranking.html",score=score[means],user=name,means=means,user_data=user_data)



#################################################################################################
#/viaに関する関数
#送られてくる値は、所要時間、目的地、出発地点、キーワード
#出発地点名、目的地名から緯度経度を取得(Google Places Api)(get_adress関数で検索(F12で飛べます))
#出発地点、目的地の緯度経度、移動手段、所要時間、キーワードから経由地を検索(search_place関数(F12で飛べます))
#3つ経由地を取り出す
#取り出した経由地を含めたルートの所要時間、道のりを取得(suggest_via関数)(Google DistanceMatrix Api)
#経由地がお気に入り指定されているかを確認する
#お気に入りにしていたら1,していなかったら0を配列に入れる
#ログイン中のユーザーのお気に入り指定した経由地をすべて取り出し、経由地と比較。もし同じものがあれば1に変化させる
#ログインされているかを確認する。ログインされていなかったら1を返す
#################################################################################################
@app.route("/via", methods=["GET", "POST"])
def via_suggest():
    if request.method == "POST":
        url = []
        #HTMLから値を受け取る
        means = request.form.get("means")
        limit = request.form.get("limit")
        origin = request.form.get("origin")

        #かなり無理やりですが実装しました。
        #緯度経度を取得するボタンを押すと緯度経度が移動手段の値の後ろに | 緯度、経度　のように格納されます。
        #それを無理やり抜き出す方法です。
        if "|" in means:
            temp_means = re.split(" | ",means)
            #temp_meansには　["移動手段"," | ","緯度経度"]　のように格納されています
            means = temp_means[0]
            origin = temp_means[2]

        #フォームに値が入っていなかったらエラー出す
        keyword_list = request.form.getlist("via_btn")
        if limit.isnumeric() == False:
            return apology("所要時間を入力してください。", 400)
        if not request.form.get("origin"):
            if origin == "":
                return apology("出発地点を入力してください。",400)
        if not request.form.get("destination"):
            return apology("目的地を入力してください。",400)


        destination = request.form.get("destination")

        keyword = ""
        for keyword_list in keyword_list:
            keyword += "|" + keyword_list
        keyword = keyword[1:]
        #関数を使って施設名から住所を取得
        destination_cie = get_address(destination)
        if destination_cie == False:
            return apology("住所が見つかりませんでした。",501)
        origin_cie = get_address(origin)
        if destination_cie == False:
            return apology("住所が見つかりませんでした。",501)

        intime = route(str(origin_cie[0])+","+str(origin_cie[1]),str(destination_cie[0])+","+str(destination_cie[1]),means)
        if int(intime['rows'][0]['elements'][0]['duration']['value']) >= int(limit)*60:
            return apology("入力した時間では目的地に到着できません",400)

        limit2 = (int(limit)*60 - int(intime['rows'][0]['elements'][0]['duration']['value']))/60
        print(limit2)



        #関数をつかって経由地を検索
        suggest_place = search_place(origin_cie[0],origin_cie[1],destination_cie[0],destination_cie[1],means,limit,keyword,limit2=limit2)

        #3つ経由先を提案する
        place = random.sample(suggest_place,3)
        #目的地を選択する場合はこれを使う。
        #データベースから目的地の緯度経度を取得
        """
        destination = db.execute("SELECT * FROM test WHERE id = ?", destination)
        destination_latitude = destination[0]["latitude"]
        destination_longitude = destination[0]["longitude"]
        """

        #関数を使って経由地を提案
        if api_value == 1:
            via = suggest_via(origin,str(destination_cie[0])+","+str(destination_cie[1]),place,means,limit)
        else:
            via = suggest_via_directions(origin,str(destination_cie[0])+","+str(destination_cie[1]),place,means,limit)
        #GoogleMapのurlを生成してlistに追加
        i = 0
        while i != len(via):
            if api_value == 1:
                url.append("https://www.google.com/maps/dir/?api=1&origin="+str(origin_cie[0])+","+str(origin_cie[1])+"&destination="+str(destination_cie[0])+","+str(destination_cie[1])+"&travelmode="+ means +"&waypoints="+str(via[i]['lat'])+","+str(via[i]['lng']))
            else:
                url.append("https://www.google.com/maps/dir/?api=1&origin="+str(origin_cie[0])+","+str(origin_cie[1])+"&destination="+str(destination_cie[0])+","+str(destination_cie[1])+"&travelmode="+ means +"&waypoints="+str(via[i]['lat'])+","+str(via[i]['lng']))
            i += 1
        favorite=[0,0,0]
        #ログインされているかを確認する。ログインされていなかったら1を返す
        session_id = 0
        if len(session) == 0:
            session_id = 1
        else:
            #経由地がお気に入り指定されているかを確認する
            #お気に入りにしていたら1,していなかったら0を配列に入れる
            favorite_temp = db.execute("SELECT name FROM favorite WHERE userid = ?", session['user_id'])
            #ログイン中のユーザーのお気に入り指定した経由地をすべて取り出し、経由地と比較。もし同じものがあれば1に変化させる
            x = 0
            for cycle in via:
                for favorite_cycle in favorite_temp:
                    if cycle['name'] == favorite_cycle['name']:
                        favorite[x] = 1
                        break
                x += 1
        return render_template("via.html" ,via=via ,url=url ,means=means ,detail=place ,key=api_key ,favorite=favorite ,destination=destination ,session_id=session_id)
    else:
        return apology("パラメータが入力されていません",501)


#################################################################################################
#詳細検索
#未実装
#################################################################################################
@app.route("/detail_search", methods=["GET", "POST"])
def detail_search():
    if request.method == "POST":
        value = request.form.get("btn")
        if value == "address":
            return render_template("address_search.html")
        if value == "latlng":
            return render_template("latlng_search.html")
        if value == "keyword":
            return render_template("keyword_search.html")
        print(value)
    return render_template("detail_search.html")



#################################################################################################
#経由地候補を返す関数です。
#|緯度,経度|緯度,経度|緯度,経度　といった感じの文字列を生成(先頭の | を削除する)(経由地)
#ユーザーは　出発地点→経由地→目的地　といった感じ移動しますが、　出発地点→経由地　と　経由地→目的地　に分割する
#分割した物と移動手段から所要時間と道のりを取得(route関数 F12で飛べます)
#経由地の数だけ関だけ関数を回す
#出発地点→経由地　と　経由地→目的地　のように分割した値を足し合わせてadd_distanceとadd_durationに入れる（移動手段が車の場合は交通状況を加味した時間を入れる)
#もし取得した時間が入力値以下なら経由地候補に入れる
#APIで取得した時間は秒のため、入力値も秒に直す
#単位を整える(unit関数 F12で飛べます)
#単位を整えた値を辞書式で保存 {'add_distance' : 合計距離, 'add_duration' : 合計時間}
#placeに加えて配列 via_candidate に保存[経由地１の辞書式 , 経由地2の辞書式 ,経由地3の辞書式]
#################################################################################################
def suggest_via(origin,destination,place,means,limit):
    via_candidate = []
    via_temp = ""
    # | で区切られた場所を文字列で生成
    for cycle in place:
        via_temp += "|" + str(cycle['lat']) + "," + str(cycle['lng'])
    #|緯度,経度|緯度,経度|緯度,経度|緯度,経度|緯度,経度|緯度,経度　といった感じの文字列を生成
    #先頭の | を削除する
    via_temp = via_temp[1:]

    #関数を使って所要時間と道のりを取得
    route1 = route(origin,via_temp,means)
    route2 = route(via_temp,destination,means)
    i = 0
    #経由地検索してlistに格納した数だけ回す
    for cycle in place:
        #先ほど関数を使い所有時間と道のりを取得した関数から時間と距離を別の関数に入れる
        add_distance = round(route1['rows'][0]['elements'][i]['distance']['value'] , -2) + round(route2['rows'][i]['elements'][0]['distance']['value'] ,-2)
        #移動手段が車の時は交通情報を加味した時間を入れる
        if means == "driving":
            add_duration = route1['rows'][0]['elements'][i]['duration_in_traffic']['value'] + route2['rows'][i]['elements'][0]['duration_in_traffic']['value']
        else:
            add_duration = route1['rows'][0]['elements'][i]['duration']['value'] + route2['rows'][i]['elements'][0]['duration']['value']
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




@app.route("/login", methods=["GET", "POST"])
def login():
    #　ユーザーidをクリアする
    session.clear()
    username = request.form.get("username")
    password = request.form.get("password")
    # POSTの場合
    if request.method == "POST":
        # ユーザーネームが入力されていない
        if not username:
            return apology("ユーザーネームを入力してください", 403)
        # パスワードが入力されていない
        elif not password:
            return apology("パスワードを入力してください", 403)

        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (username,))
        users = db.fetchone()
        db.execute("SELECT * FROM tenantusers WHERE username = ?", (username,))
        tenantusers = db.fetchone()
        con.close()
        # ユーザーネームとパスワードが正しいか確認
        if users != None:
            if check_password_hash(users[2], password):
                # ユーザーを記憶する
                session["user_id"] = users[0]
                #メッセージ
                flash("ログインしました")
                return redirect("/")
        elif tenantusers != None:
            if check_password_hash(tenantusers[2], password):
                session["tenant_user_id"] = tenantusers[0]
                #メッセージ
                flash("ログインしました")
                return redirect("/tenanthome")
        else:
            return apology("ユーザネームが無効です", 403)

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
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return apology("ユーザーネームを入力してください", 400)
        # ユーザーネームが既に使われている
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("SELECT * FROM users where username=?", (username,))
        user = db.fetchone()
        if user != None:
            return apology("このユーザーネームは既に使われています", 400)
        # パスワードが入力されていない
        elif not password:
            return apology("パスワードを入力してください", 400)
        # パスワードが一致しない
        elif password != request.form.get("confirmation"):
            return apology("パスワードが一致しません", 400)
        con.close()
        password = generate_password_hash(password)
        # データベースに入れる
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, password))
        con.commit()
        con.close()
        #メッセージ
        flash("登録が完了しました")
        # ログインページに送る
        return redirect("/login")
    else:
        return render_template("register.html")

#################################################################################################
#単位を整える関数です
# 入ってくる値は　距離→m　時間→分?(分の法は確証がないので後で確認します。)

#距離
#もし1000m以上であれば、kmに値を変換して文字列として単位をつけて保存

#時間
#商とあまりをつかって変換する
#二重構造で一重目は分が60分以上であるか
#60分以上であるならば　時　に変換する　余りは分のまま
#二重目は24時間以上であるか
#変換した　時　が　24以上であれば　日　に変換　余りは　時　のまま
#単位付きの文字列を返す
#################################################################################################
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
        add_distance = str('{:.1f}'.format(km)) + "km"
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




#################################################################################################
#施設名から緯度経度に変換する関数(Google geocodeAPI)
#{key:apiキー,adress:場所,言語:日本語}といった具合でパラメーターを設定
#緯度経度と取り出して返す
#################################################################################################
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

    #取得したデータから緯度経度を抽出し、　緯度,経度　の形にして変数に保存する
    #address = str(answer['results'][0]['geometry']['location']['lat']) + "," + str(answer['results'][0]['geometry']['location']['lng'])
    return answer['results'][0]['geometry']['location']['lat'],answer['results'][0]['geometry']['location']['lng']



#################################################################################################
#経由地を探す関数

#送られてくる値は　出発地点の緯度経度　目的地の緯度経度　移動手段　所要時間　キーワード
#移動手段によって検索する経由地の半径を設定する(車→250m/min 自転車→166m/min 歩き→66m/min)
#最大半径は50kmのため それ以上ならば50kmに設定
#円の中点は目的地と出発地点の中心
#経由地を検索　パラメーターは　目的地と出発地点の中心座標　半径　キーワード　言語(日本語)
#temp1に緯度経度　temp2に施設名　temp3にGoogleMapの評価　temp4に住所　temp5にGoogleで写真を判別するための文字列を保存 {'キー'：値}
#temp2 3 4 5 をtemp1に結合 {'location':値,'name':値,'rating':値,'vicinity':値,'photo_place':値}
#suggest_placeに配列として保存して返す
#################################################################################################
def search_place(original_latitude,original_longitude,destination_latitude,destination_longitude,means,limit,keyword,limit2):
    client = googlemaps.Client(api_key) #インスタンス生成
    #loc = {'lat': 35.6288505, 'lng': 139.65863579999996} # 軽度・緯度を取り出す

    #目的地とスタート地点の中心を起点とする
    #loc = {'lat': str((float(original_latitude) + float(destination_latitude))/2), 'lng': str((float(original_longitude) + float(destination_longitude))/2)}
    #それぞれの手段によって半径を変える
    if means == 'driving':
        radius = 360 * int(limit2)/60
        ra = 5 / 60 * int(limit2) /60
    if means == 'bicycling':
        radius = 250 * int(limit2)/60
    if means == 'walking':
        radius = 100 * int(limit2)/60
    #placesAPIで検索する際の最大の半径は50kmなので50kmまでに統一する
    if radius > 500000:
        radius = 500000

    print(original_latitude)
    print(original_longitude)
    try:
        housenn = - (float(original_longitude) - float(destination_longitude)) / (float(original_latitude) - float(destination_latitude))
        tyuutenn_lat = (float(original_latitude) + float(destination_latitude))/2
        tyuutenn_lng = (float(original_longitude) + float(destination_longitude))/2
        degree = math.atan(housenn)
        lat_temp = ra * math.cos(degree) + tyuutenn_lat
        lng_temp = ra * math.sin(degree) + tyuutenn_lng
        loc = {'lat':str(lat_temp), 'lng':str(lng_temp)}
        print(loc)
    except ZeroDivisionError:
        loc = {'lat': str((float(original_latitude) + float(destination_latitude))/2), 'lng': str((float(original_longitude) + float(destination_longitude))/2)}

    radius1 = radius / 2
    print(radius)
    print(radius1)
    #結果を表示
    place_results = client.places_nearby(location=loc, radius=radius ,keyword=keyword ,language='ja')
    place_results_pull = client.places_nearby(location=loc, radius=radius1 ,keyword=keyword ,language='ja')
    results = []
    suggest_place = []
    results_pull = []
    #実行結果を保存
    for place_result in place_results['results']:
        results.append(str(place_result))
    for place_result_pull in place_results_pull['results']:
        results_pull.append(str(place_result_pull))

    print(str(results))
    results_temp = set(results)-set(results_pull)
    results.clear()
    print(results)
    for cycle in results_temp:
        results.append(ast.literal_eval(cycle))

    #それぞれの経由地の緯度経度、名前、評価、住所を辞書式で保存
    for temp in results:
        #temp = random.choice(results)
        #results.remove(temp)
        #緯度経度
        temp1 = temp['geometry']['location']
        #名前
        temp2 = {'name':temp['name']}
        #評価（なければ無を代入)
        if not 'rating' in temp.keys():
            temp3=""
        else:
            temp3 = {'rating':temp['rating']}
        temp4 = {'vicinity':temp['vicinity']}
        #写真の文字列(なければ無を代入)
        if not 'photos' in temp.keys():
            temp5={'photo_reference':''}
        else:
            temp5 = {'photo_reference':temp['photos']}
        #temp1に結合
        temp1.update(temp2)
        temp1.update(temp3)
        temp1.update(temp4)
        temp1.update(temp5)
        #配列に保存
        suggest_place.append(temp1)
    return suggest_place



#################################################################################################
#distance matrix apiで距離・時間を取得する関数

#パラメーターを設定
#結果をjson形式で受け取り、プログラムが読めるかたちに変換する
#################################################################################################
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

@app.route("/test")
def test():
    print(route("東京駅","東京ドーム","walking"))
    return render_template("test.html")


@app.route("/mypage")
def mypage():
    userid= session["user_id"]
    con = sqlite3.connect('./map.db')
    db = con.cursor()
    db.execute("SELECT * FROM users where id=?", (userid,))
    user = db.fetchone()
    con.close()
    return render_template("mypage.html",user=user)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        userid = session["user_id"]
        nickname = request.form.get("nickname")
        if db.execute("SELECT icon FROM users WHERE id = ?",userid)[0]["icon"] == None:
            filepath=None
        else:
            filepath=db.execute("SELECT icon FROM users WHERE id = ?",userid)[0]["icon"]

        img = request.files['imgfile']
        if img:
            filepath = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/icon', filepath))

        db.execute("UPDATE users SET display_name=(?), icon=(?) WHERE id=(?)",nickname,filepath,userid)
        return redirect("/mypage")
    else:
        userid = session["user_id"]
        users = db.execute("SELECT display_name,icon FROM users WHERE id = (?)", userid)
        return render_template("profile.html",users=users)




#################################################################################################
#履歴を読み込む関数
#データベースからユーザーidに一致する物を返す
#################################################################################################
@app.route("/history")
def history():
    #history = db.execute("SELECT  FROM histories WHERE user_id = ?", session["user_id"])
    if request.method == "POST":
        means = request.form.get('means')
    #デバッグ用
    else:
        means = "driving"

    history = db.execute("SELECT * FROM history WHERE userid=?",session['user_id'])
    return render_template("history.html", history = history)



#################################################################################################
#お気に入りを表示する関数
#favorite.htmlを書き換えてよいかわからなかったため、favorite_test.htmlを表示するようにしています。
#################################################################################################
@app.route("/favorite")
# お気に入りを表示
def favorite():
    #favorite = db.execute("SELECT name, url FROM favorites WHERE user_id =?", session["user_id"])
    userid = session['user_id']
    favorite = db.execute("SELECT * FROM favorite WHERE userid=?",userid)
    return render_template("favorite_test.html", favorite = favorite)



#################################################################################################
#履歴に保存する関数
#HTMLから　url:値name:値distance:値means:値duration:値destination:値　といった形で送られてくるので re.split　で分割して値を取り出す
#値をデータベースに保存する
#################################################################################################
@app.route("/add_history" ,methods=["GET","POST"])
def add_history():
    history =request.form.get("place")
    history = re.split('url:|name:|distance:|kmmeans:|duration:|destination:',history)
    print(history)
    dt_now = time.time()
    db.execute("INSERT INTO history (userid ,url ,used_at ,required_at ,distance ,way ,first ,second) VALUES ( ? ,? ,? ,? ,? ,? ,? ,? )",
    session["user_id"] ,history[1] ,dt_now ,history[5] ,history[3] ,history[4] ,history[6] ,history[2])
    return redirect(history[1])



@app.route("/tenantregister", methods=["GET", "POST"])
def tenantregister():
    # POSTの場合
    if request.method == "POST":
        # ユーザーネームが入力されていない
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return apology("ユーザーネームを入力してください", 400)
        # ユーザーネームが既に使われている
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("SELECT * FROM tenantusers where username=?", (username,))
        tenantuser = db.fetchone()
        db.execute("SELECT * FROM users where username=?", (username,))
        user = db.fetchone()
        if user != None or tenantuser != None:
            return apology("このユーザーネームは既に使われています", 400)
        con.close()
        # パスワードが入力されていない
        if not password:
            return apology("パスワードを入力してください", 400)
        # パスワードが一致しない
        elif password != request.form.get("confirmation"):
            return apology("パスワードが一致しません", 400)
        con.close()
        password = generate_password_hash(password)
        # データベースに入れる
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("INSERT INTO tenantusers (username, hash) VALUES(?, ?)", (username, password))
        con.commit()
        con.close()
        #メッセージ
        flash("登録が完了しました")
        # ログインページに送る
        return redirect("/login")
    else:
        return render_template("tenantregister.html")

@app.route("/tenanthome", methods=["GET", "POST"])
def tenanthome():
    # POSTの場合
    if request.method == "POST":
        userid = session["tenant_user_id"]
        name = request.form.get("name")
        tel = request.form.get("tel")
        postcode = request.form.get("postcode")
        addr= request.form.get("addr")
        img = request.files['imgfile']

        # データベースに入れる
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("SELECT * FROM tenants WHERE id = ?",(userid,))
        tenant = db.fetchone()
        con.close()
        if tenant == None:
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("INSERT INTO tenants (id, name, post, addr,number) VALUES(?, ?, ?, ?, ?)", (userid, name, postcode, addr, tel))
            con.commit()
            con.close()
            #メッセージ
            flash("登録が完了しました")
        else:
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("UPDATE tenants SET name=?, post=?, addr=?, number=? WHERE id=?", (name,postcode,addr,tel,userid))
            con.commit()
            con.close()
            #メッセージ
            flash("変更が完了しました")
        # 画像がある場合画像を追加する
        if img:
            filepath = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/tenantimg', filepath))
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("UPDATE tenants SET photo=? WHERE id=?",(filepath,userid))
            con.commit()
            con.close()
        # ログインページに送る
        return redirect("/tenanthome")
    else:
        userid=session["tenant_user_id"]
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("SELECT * FROM tenants WHERE id = ?",(userid,))
        tenants = db.fetchone()
        con.close()
        return render_template("tenanthome.html",tenants=tenants)

@app.route("/keyword", methods=["GET", "POST"])
def keyword():
    if request.method == "POST":
        userid=session["tenant_user_id"]
        mode = int(request.form.get("mode"))
        if mode == 1:
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("UPDATE tenantkeys SET 'set'=? WHERE id=?", (mode,userid))
            con.commit()
            con.close()
        elif mode == 0:
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("UPDATE tenantkeys SET 'set'=? WHERE id=?", (mode,userid))
            con.commit()
            con.close()
        return redirect("/keyword")
    else:
        userid=session["tenant_user_id"]
        con = sqlite3.connect('./map.db')
        db = con.cursor()
        db.execute("SELECT * FROM tenantkeys WHERE id = ?",(userid,))
        tenantkey=db.fetchone()
        con.close()
        if tenantkey == None:
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("INSERT INTO tenantkeys (id) VALUES(?)",(userid,))
            con.commit()
            db.execute("SELECT * FROM tenantkeys WHERE id = ?",(userid,))
            tenantkey=db.fetchone()
            con.close()
        if tenantkey[3] == 0:
            with open("keyword.txt") as f:
                keyword = f.readlines()
            key_list = [str.rstrip() for str in keyword]
            list = len(key_list)
            rand = random.randint(0,list)
            key = key_list[rand]
            print(key)
            con = sqlite3.connect('./map.db')
            db = con.cursor()
            db.execute("UPDATE tenantkeys SET 'keyword'=?,'keycount'=? WHERE id=?", (key,1,userid))
            con.commit()
            db.execute("SELECT * FROM tenantkeys WHERE id = ?",(userid,))
            tenantkey=db.fetchone()
            con.close()
        return render_template("keyword.html",tenantkey=tenantkey)



#################################################################################################
#index画面に表示する経由地スポットを表示するための関数
#緯度経度を取得していればその地点の、していなければ東京駅を中心としたスポットを返す
#車で60分以内に行ける地点を表示する
#geoはHTMLの　現在地から出発するボタン　と　出発地点のフォーム　の表示切り替えに使う
#################################################################################################
@app.route("/geo", methods=["GET","POST"])
def geo():
    if request.method == "POST":
        lat = request.form['lat']
        long = request.form['long']
        keyword = ""
        geo = 1
        place = search_place(lat,long,lat,long,"driving",60,keyword)
        return render_template("index.html",lat=lat ,long=long ,place=place ,key=api_key ,geo=geo)
    else:
        lat = 35.1706431
        long = 136.8816945
        keyword = ""
        geo = 1
        place = search_place(lat,long,lat,long,"driving",60,keyword)
        return render_template("index.html",lat=lat ,long=long ,place=place ,key=api_key ,geo=geo)



#################################################################################################
#お気に入りに追加する関数
#送られてくる文字列は　_=_ で区切ってあるので　_=_　で分割する
#送られてくる辞書式や配列の値は文字列型として送られてきてキーを使った検索ができないため苦戦中
#################################################################################################
@app.route("/add_favorite", methods=["GET", "POST"])
def add_favorite():
    if request.method == "POST":
        #favorite_temp = request.json['url']
        favorite_temp = request.form.get("place")
        #値を取り出す
        favorites = re.split(" _=_ ",favorite_temp)
        length = favorites[3].count("https")
        #受け取った値は文字列になってしまっているので気合で配列に戻す
        if length >= 2:
            favorites[3] = favorites[3][1:]
            favorites[3] = favorites[3][:-1]
            favorites[3] = re.split("', '",favorites[3])
            for b in range(length):
                favorites[3][b] = "'" + favorites[3][b] + "'"
                favorites[3][b] = favorites[3][b][1:]
                favorites[3][b] = favorites[3][b][:-1]
            favorites[3][0] = favorites[3][0][1:]
            favorites[3][2] = favorites[3][2][:-1]
        else:
            favorites[3] = favorites[3][2:]
            favorites[3] = favorites[3][:-2]
        print(favorites[3][0])

        if favorites[0] == "add":
            db.execute("INSERT INTO favorite (userid ,name ,url) VALUES (? ,? ,?)" ,session['user_id'] ,favorites[1] ,favorites[3][int(favorites[7][1])])
        else:
            db.execute("DELETE FROM favorite WHERE userid=? AND name=?" ,session['user_id'] ,favorites[1])

        favorites[5] = favorites[5][1:][:-1]
        favorites[5] = re.split('}, {',favorites[5])
        dict_detail = []
        for y in range(length):
            favorites[5][y] = "{" + favorites[5][y] + "}"
        favorites[5][0] = favorites[5][0][1:]
        favorites[5][2] = favorites[5][2][:-1]
        for cycle in favorites[5]:
            dict_detail.append(ast.literal_eval(cycle))
        #経由地がお気に入り指定されているかを確認する
        #お気に入りにしていたら1,していなかったら0を配列に入れる
        favorite=[0,0,0]
        favorite_temp = db.execute("SELECT name FROM favorite WHERE userid = ?", session['user_id'])
        #ログイン中のユーザーのお気に入り指定した経由地をすべて取り出し、経由地と比較。もし同じものがあれば1に変化させる
        #ログインされているかを確認する。ログインされていなかったら1を返す
        session_id = 0
        if len(session) == 0:
            session_id = 1
        else:
            #経由地がお気に入り指定されているかを確認する
            #お気に入りにしていたら1,していなかったら0を配列に入れる
            favorite_temp = db.execute("SELECT name FROM favorite WHERE userid = ?", session['user_id'])
            #ログイン中のユーザーのお気に入り指定した経由地をすべて取り出し、経由地と比較。もし同じものがあれば1に変化させる
            x = 0
            for cycle in dict_detail:
                for favorite_cycle in favorite_temp:
                    if cycle['name'] == favorite_cycle['name']:
                        favorite[x] = 1
                        break
                x += 1
        return render_template("via.html" ,via=dict_detail ,url=favorites[3] ,means=favorites[4] ,detail=dict_detail ,key=api_key ,favorite=favorite ,session_id=session_id)





"""
#################################################################################################
#Distance Matrix Apiだとなぜかマップの値とのズレが発生するのでdistance durationAPIで処理してみます。
#################################################################################################
@app.route("/via", methods=["GET", "POST"])
def via_suggest():
    url = []
    #HTMLから値を受け取る
    destination = request.form.get("destination")
    means = request.form.get("means")
    limit = request.form.get("limit")
    origin = request.form.get("origin")

    #フォームに値が入っていなかったらエラー出す
    keyword_list = request.form.getlist("via_btn")
    if limit.isnumeric() == False:
        return apology("所要時間を入力してください。", 400)
    if not request.form.get("origin"):
        if origin == "":
            return apology("出発地点を入力してください。",400)
        if not request.form.get("destination"):
            return apology("目的地を入力してください。",400)


    destination = request.form.get("destination")


    #関数を使って経由地を一つ提案
    via = suggest_via_duration("東京駅",str(destination_latitude)+","+str(destination_longitude),means,limit)

    #GoogleMapのurlを生成してlistに追加
    i = 0
    while i != len(via):
        url.append("https://www.google.com/maps/dir/?api=1&origin=名古屋駅&destination="+str(destination_latitude)+","+str(destination_longitude)+"&travelmode="+ means +"&waypoints="+str(via[i]['latitude'])+","+str(via[i]['longitude']))
        i += 1

    return render_template("via.html" ,via=via ,url=url)
"""


def suggest_via_directions(origin,destination,place,means,limit):
    via_candidate = []

    #dbから読み取った値を一つずつ処理していく
    #処理はroundで移動距離、移動時間を取得して足し算、足した値が入力した値より小さければlistに格納する
    for cycle in place:
        print(cycle)
        route1 = route_directions("名古屋駅",str(cycle['lat'])+","+str(cycle['lng']),means)
        route2 = route_directions(str(cycle['lat'])+","+str(cycle['lng']),destination,means)
        print(route1)
        print(route2)
        #所要時間と移動距離を足し算する
        add_duration = duration_function(route1[1],route2[1])
        add_distance = distance_function(route1[0],route2[0])
        print(add_duration)
        print(add_distance)

        #もし制限時間以内に経由できるのならばlistに加える
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
def route_directions(origin,destination,means):

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
