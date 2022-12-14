# FLATTO
#### Video Demo:　https://www.youtube.com/watch?v=3P05movHN18&ab_channel=AS116-%E9%9D%92%E6%9C%A8%E6%9C%AA%E6%9D%A5
#### Description:

<br>

# アプリの説明
## 想い
目的地を入力すると遠回りするルートを提案するという、最適化が求められる現代においてあえて最適化を求めないサービスを提供したいと考えこのアプリを制作しました。<br>
このサービスは、エンジニアなど発想力を必要とする人に対して新たな発見ができるように様々な経験を提供したり、散歩やドライブをしたい人に向けて交通手段や所要時間などに応じたルートを提案します。<br>
## 機能概要
このアプリでは出発地(又は現在地)と目的地を入力し、所要時間や移動手段を指定すると所要時間内に行くことができる経由地一覧を閲覧することができます。経由地を確定すると実際のマップが表示され、案内を開始できます。<br>
アプリにログインすると、移動距離に応じたランキング機能や経由地のお気に入り機能、経由地の履歴など様々な機能を使えるようになっています。<br>
ユーザだけではなく経由地として登録したい方のためのページも作成してあります。Googlemapに乗っていないお店の場合は情報を入力することで、経由地登録ができるようになっています。<br>
<br><br><br>

## テスト用アカウント
* ユーザーアカウント<br>
ID: S04<br>
PASS: teamprintai<br>
* 店舗用アカウント<br>
ID: tenant<br>
PASS: aa<br>
<br><br><br>

## 利用方法
このアプリケーションの利用方法を説明します
* 経由地スポット検索<br>
ユーザー登録がめんどくさい人や、現在地情報を渡したくない人でも使えるように製作しました。<br>
経由地スポットを検索するためには、目的地・出発地点・所要時間・移動手段を最低限決める必要があります。<br>
「現在地から出発する」というボタンを押すことによって現在地を出発地点に設定することも可能です。<br>
また、フォームの下にあるチェックボックスにチェックを入れることによって経由地スポットの絞り込みを行うことができます<br>
チェックボックスはクリアボタンを押すことによってクリアすることができます。<br>
これらの内容を入力し終わった後、検索ボタンを押すと入力した条件に従って経由地を検索します。<br>
Google Map APIを使用して経由地を検索しているため、DBにない経由地も検索でき海外の経由地スポットを入力しても使うことができます。<br>
検索するとGoogleMapでの評価・口コミ・周辺の経由地スポット・出発地から経由地を含めた目的地までのルートを含めた地図・MAPで開くボタンが表示されます。<br>

* 現在地周辺の経由地スポットを表示する機能<br>
検索画面の左下に表示されています。<br>
「現在地から出発する」ボタンを押すことことによって現在地周辺の経由地スポットを取得することができます。<br>
また、「WEBで開く」ボタンを押すことによってブラウザのサーチバーに経由地名を入力されたページに飛ぶことができます。<br>

* お気に入り機能<br>
ログインしたユーザーのみが使える経由地スポットをお気に入りに登録する機能です。<br>
検索した経由地スポット名の下にある「お気に入りに登録する」ボタンを押すことによってお気に入りに登録することができます。<br>
お気に入りを解除した場合は「お気に入りに登録する」ボタンが「お気に入りを解除する」というボタンに代わっていると思うので、それを押すことによってお気に入りを解除することができます。<br>

* 周辺の経由地スポットを検索する機能<br>
検索して出てきた経由地スポットの周辺の経由地スポットを評価・写真・住所・名前とともに表示します。<br>
「経由地を変更する」というボタンを押すことによって経由地を変更することができます。<br>

* 履歴機能<br>
使った経由地スポットを履歴に保存する機能です<br>
「MAPを開く」ボタンを押すとDBに履歴として保存されます。<br>

* ランキング機能<br>
ランキングを表示します。<br>
ランキングは履歴テーブルから引っ張ってきたデータを参照して計算します。<br>
アイコンとニックネーム(ここに表示されるのはユーザーネームではありません。)が表示されます。<br>
アイコンが設定されていない場合はロゴが、名前が設定されていない場合はUnknownと表示されるようになっています。<br>

* ポイント機能<br>
 経由地の店舗に表示されているキーワードを入力するとポイントがたまっていきます。<br>
 ポイントを利用してアプリ上のアイテムを購入できるようにするか、店舗で割引として使えるようにするかは検討中です。<br>

### 店舗用画面
* テナント追加<br>
 GoogleMapに載っていないなど経由地として登録されていない場合、店舗情報(店舗名・住所・郵便番号・電話番号)を入力することで経由地として登録することができます。<br>

* キーワード画面<br>
 ユーザのポイント画面で入力する際のキーワードが日替わりで表示されます。<br>
 キーワード入力モードのスイッチをオンにすると店舗側がキーワードを設定することもできます。<br>
<br><br><br>

## 目指した問題解決
* 散歩やドライブに対するハードルを下げる(どこに寄っていくか迷わない)<br>
* アイディアを必要とする人たちへの環境提供(新たな景色を見ることでアイディアを沸かせる)<br>
* デジタルデトックス(散歩やドライブで気分転換)<br>
* 誰でも使える(ログインしなくても使えるので、機械系が苦手な方でも使いやすい)<br>
<br><br><br>


## 実装予定の機能

* 詳細検索機能<br>
* ポイント機能<br>
* 交通状態によって経由地を検索するための中心地を変更する。<br>
<br><br><br>

## 動作方法
動作環境　CS50のコードスペース<br>
使用技術<br>
データベース:SQLite<br>
言語:Python HTML CSS JavaScript<br>
フレームワーク:Flask Bootstrap<br>　
<br>
git cloneをした後、mapフォルダ直下に APIkey.txt というテキストファイルを作成し、テキストファイル内にGoogleMapAPIのキーの文字列を記述<br>
ターミナルを開き、　pip install googlemapsとpip install schedule　というコマンドを実行する<br>
その後、flask run　というコマンドを実行し、ターミナルに出力されたURLにアクセスしてください。<br>
<br><br><br>
