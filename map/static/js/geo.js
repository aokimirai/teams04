// ボタンを押した時の処理
document.getElementById("btn").onclick = function(){
    // 位置情報を取得する
    navigator.geolocation.getCurrentPosition(successCallback, errorCallback);
};

// 取得に成功した場合の処理
function successCallback(position){
    // 緯度を取得し画面に表示
    var latitude = position.coords.latitude;
    document.getElementById("latitude").innerHTML = latitude;
    // 経度を取得し画面に表示
    var longitude = position.coords.longitude;
    document.getElementById("longitude").innerHTML = longitude;
    send (latitude, longitude);
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

  // フォームの入力値を送信
  fetch( '', {
    method: 'POST',
    body: fd
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
  })
  .catch((error) => {
    console.error(error);
  });
}