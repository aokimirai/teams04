$(".addtofavorite").click(function(){
    var favorite_start = JSON.parse(localStorage.getItem('favorite'));
    var name = $("{{ via.name }}").text(); // 経由地名を取得
    var duration = $("{{ via.add_duration }}").text(); // 所要時間を取得
    var distance = $("{{ via.add_distance }}").text(); // 道のりを取得
    var url = $("{{ url[a.cnt] }}").text(); // URLを取得

    var favorite = [{
        name = name
        duration = duration
        distance = distance
        url = url
    }];


    if (favorite_start) {
        for(i=0;i<10;i++) {
            if (favorite_start[i] && favorite[0].url !== favorite_start[i].url) {
                favorite.push(favorite_start[i]);
            }
        }
    }
    localStorage.setItem('favorite',JSON.stringify(favorite));
    addFavorite();
});

function addFavorite() {
    $(".removefavorite").removeClass('hidden');
    $(".addtofavorite").addClass('hidden');
}

$(".removefavorite").click(function(){
    var favorite_pages_start = JSON.parse(localStorage.getItem('favorite'));
    var favorite_pages = [];
    if (favorite_pages_start) {
        for(i=0;i<10;i++) {
            if (favorite_pages_start[i] && CCM_CID !== favorite_pages_start[i].url) {
                favorite_pages.push(favorite_pages_start[i]);
            }
        }
    }
    localStorage.setItem('favorite_pages',JSON.stringify(favorite_pages));
    removeFavorite();
});