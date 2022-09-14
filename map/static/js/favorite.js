$(".addtofavorite").click(function(){
    var favorite_pages_start = JSON.parse(localStorage.getItem('favorite_pages'));
    var name = $("{{ via.name }}").text(); // ページのタイトルを取得
    var duration = $("{{ via.add_duration }}").text(); // ページのタイトルを取得
    var distance = $("{{ via.add_distance }}").text(); // ページのタイトルを取得
    var url = $("{{ url[a.cnt] }}").text(); // ページのタイトルを取得

    var favorite = [{
        name = name
        duration = duration
        distance = distance
        url = url
    }];


    if (favorite_start) {
        for(i=0;i<10;i++) {
            if (favorite_pages_start[i] && favorite_pages[0].url !== favorite_pages_start[i].url) {
                favorite_pages.push(favorite_pages_start[i]);
            }
        }
    }
    localStorage.setItem('favorite_pages',JSON.stringify(favorite_pages));
    addFavorite();
});

function addFavorite() {
    $(".favoritedmark").removeClass('fade');
    $(".removefavorite").removeClass('hidden');
    $(".addtofavorite").addClass('hidden');
}