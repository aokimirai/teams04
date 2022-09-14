$(".addtofavorite").click(function(){
    var favorite_start = JSON.parse(localStorage.getItem('favorite'));

    var favorite = [{
        name = {{ via.name }}
        duration = {{ via.add_duration }}
        distance = {{ via.add_distance }}
        url = {{ url[a.cnt] }}
    }];


    if (favorite_start) {
        for(i=0; ;i++) {
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

function removeFavorite() {
    $(".removefavorite").addClass('hidden');
    $(".addtofavorite").removeClass('hidden');
}

var favorite = JSON.parse(localStorage.getItem('favorite'));
var selected = false;
if (favorite) {
    for(i=0;i<;i++) {
        if (!selected && favorite[i] && !isNaN(favorite[i]['url'])) {
            if (CCM_CID == favorite[i]['url']){
                selected = true;
            }
        }
    }
}
if(selected) {
    addFavorite();
}