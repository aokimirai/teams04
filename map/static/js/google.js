var n;
var tmp = document.getElementsByClassName("btn") ;
function buttonClick(n){
  btn[n - 1].classList.toggle('btn-outline-info');
  btn[n - 1].classList.toggle('btn-info');
}