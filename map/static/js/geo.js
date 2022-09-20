// ボタンを押した時の処理
document.getElementById("btn_target").onclick = function(){
    // 位置情報を取得する
    navigator.geolocation.getCurrentPosition(successCallback, errorCallback);
    window.location.href = '/geo';
};

// 取得に成功した場合の処理
function successCallback(position){
    var latitude = position.coords.latitude;
    var longitude = position.coords.longitude;
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
  fetch( '/geo', {
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