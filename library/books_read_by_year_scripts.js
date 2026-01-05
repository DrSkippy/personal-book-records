$(document).ready(function () {
    topnavbar();
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    var root_url = baseApiUrl + "/books_read";
    $.ajaxSetup({async: false});  // suppress async so the summary row is always at the bottom
    let years = [];
    if (urlParams.has("year")) {
        years.push(urlParams.get('year'));
    } else {
        years = generateYearsArray(1983);
    }
    var url;
    const idArray = [];
    for(const year of years) {
        const url1 = baseApiUrl + "/summary_books_read_by_year/" + year;
        $.getJSON(url1, function (data) {
            var obj = data['data'];
            for (var i = 0; i < obj.length; i++) {
                var tr = "<tr class='summary-row'>" +
                    "<td colspan='3'>Year: " + obj[i][0] +
                    "<td colspan='3'>Pages: " + obj[i][1] + " &nbsp;&nbsp;(" + obj[i][2] + " books)</td></tr>";
                $("#mytable-sorted").append(tr);
            }
        });
        url = root_url + "/" + year
        $.getJSON(url, function (data) {
            var obj = data['data'];
            idArray.push(obj.map(function (x) {
                return x[0];
            }));
            for (var i = 0; i < obj.length; i++) {
                var tr = "<tr>" +
                    "<td><button class='book-id-button' onclick=\"setval(" + obj[i][0] + ")\">" +
                    obj[i][0].toString() + "</button><a href=\"/js_reports/carousel.html?centerbookid=" +
                    obj[i][0].toString() + "&windowsize=3\"> C </a></td>" +
                    "<td>" + obj[i][1] + "</td>" +
                    "<td>" + obj[i][2] + "</td>" +
                    "<td>" + obj[i][3] + "</td>" +
                    "<td>" + obj[i][7] + "</td>" +
                    "<td>" + obj[i][13] + "</td></tr>";
                $("#mytable-sorted").append(tr);
            }
        });
    }
    const idArrayURLEnc = idArray.map(function(x) {return "idArray=" + x.toString();}).join("&");
    console.log(idArray);
    console.log(idArrayURLEnc);
    document.getElementById("updatereadnotesurl").innerHTML = '<a href=' +
        '"' + baseApiPath + 'js_reports/update_read_notes.html?' + idArrayURLEnc + '">' +
        'Update book read notes for items in this list</a>';
    createDetailTableRows();
    $.ajaxSetup({async: true});  // suppress async so the summary row is always at the bottom
});

function generateYearsArray(startYear) {
  const currentYear = new Date().getFullYear();
  const years = [];

  for (let year = startYear; year <= currentYear; year++) {
    years.push(year);
  }

  return years;
};