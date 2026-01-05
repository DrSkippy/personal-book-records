$(document).ready(function () {
    topnavbar();
    /*
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    */
    var url = baseApiUrl + "/books_search?Recycled=0&Location=Main";
    $.ajaxSetup({async: false});  // suppress async so the summary row is always at the bottom
    var idArray;
    $.getJSON(url, function (data) {
        var obj = data['data'];
        idArray = obj.map(function (x) {
            return x[0];
        });
        for (var i = 0; i < obj.length; i++) {
            var checkedString = ((parseInt(obj[i][10]) == 1) ? "checked" : "");
            console.log(checkedString);
            var tr = "<tr>" +
                "<td><button class='book-id-button' onclick=\"setval(" + obj[i][0] + ")\">" + obj[i][0].toString() + "</button>" +
                "<a href=\"/js_reports/carousel.html?centerbookid=" +
                    obj[i][0].toString() + "&windowsize=3\"> C </a></td>" +
                "<td>" + obj[i][1] + "</td>" +
                "<td>" + obj[i][2] + "</td>" +
                "<td>" + obj[i][3] + "</td>" +
                "<td>" + obj[i][6] + "</td>" +
                "<td>" + obj[i][13] + "</td>" +
                "<td><input onclick=\"changeCheckStatus(this, " + parseInt(obj[i][0]) + 
		")\" type=\"checkbox\" id=\"recycled\" name=\"recycled\"" + checkedString + "></td></tr>";
            $("#mytable").append(tr);
        }
    });
    const idArrayURLEnc = idArray.map(function (x) {
        return "idArray=" + x.toString();
    }).join("&");
    console.log(idArray);
    console.log(idArrayURLEnc);
    document.getElementById("updatereadnotesurl").innerHTML = '<a href=' +
        '"' + baseApiPath + 'js_reports/update_read_notes.html?' + idArrayURLEnc + '">' +
        'Update book read notes for items in this list</a>';
    createDetailTableRows();
    $.ajaxSetup({async: true});  // suppress async so the summary row is always at the bottom
});

function changeCheckStatus(cb, bookCollectionID) {
    var url = baseApiUrl + "/update_book_note_status";
    var status = (cb.checked)? 1 : 0;
    var params = "{\"BookCollectionID\": " + bookCollectionID.toString() + ",\"Recycled\":" + status.toString() + "}";
    console.log(params);
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
    xhr.setRequestHeader('x-api-key', apiKey);
    xhr.onreadystatechange = function () {
        console.log(xhr.responseText);
    };
    xhr.send(params);
}
