// ボタンを押した時の処理
document.getElementById("btn").onclick = function(){
    // 位置情報を取得する
    navigator.geolocation.getCurrentPosition(successCallback, errorCallback);
    send (latitude, longitude);
};

// 取得に成功した場合の処理
function successCallback(position){
    // 緯度を取得し画面に表示
    var latitude = position.coords.latitude;
    document.getElementById("latitude").innerHTML = latitude;
    // 経度を取得し画面に表示
    var longitude = position.coords.longitude;
    document.getElementById("longitude").innerHTML = longitude;
};

// 取得に失敗した場合の処理
function errorCallback(error){
    alert("位置情報が取得できませんでした");
};

// APIに緯度と経度を送る
function send (latitude, longitude){
  // FormDataオブジェクトの初期化
  const fd = new FormData();

  // FormDataオブジェクトにデータをセット
  fd.append('lat', latitude);
  fd.append('long', longitude);

  $.ajax({
    url: '/gps',
    type: 'POST',
    data: fd ,
    contentType: false,
    processData: false,
    success: function(data, dataType) {
        //非同期で通信成功時に読み出される [200 OK 時]
        console.log('Success', data);
    },
    error: function(XMLHttpRequest, textStatus, errorThrown) {
        //非同期で通信失敗時に読み出される
        console.log('Error : ' + errorThrown);
    }
});
}