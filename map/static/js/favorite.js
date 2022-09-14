$(".addtofavorite").click(function(){
    var favorite_pages_start = JSON.parse(localStorage.getItem('favorite_pages'));
    var title = $("h1.page-title").text(); // ページのタイトルを取得
    if (!title.length) { // ↑が無い場合は、<head>のタイトルを取得
        title = document.title;
    }
    var favorite_pages = [{
        url: CCM_CID, // CCM_CIDは、concrete5 が各ページに付与しているID
        title: title,
        datetime: $.now()
    }];

    if(favorite_pages_start.length >= 10) { // 最大10個まで
        alert("お気に入りの登録数の上限に達しました。");
        return;
    }
    if (favorite_pages_start) {
        for(i=0;i<10;i++) {
            if (favorite_pages_start[i] && favorite_pages[0].url !== favorite_pages_start[i].url) {
                favorite_pages.push(favorite_pages_start[i]);
            }
        }
    }
    localStorage.setItem('favorite_pages',JSON.stringify(favorite_pages));
    addFavorite();
});