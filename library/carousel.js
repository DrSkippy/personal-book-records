let minCarouselBookId = 0;
let maxCarouselBookId = 0;
var windowSize;
var startingBookId;

$(document).ready(function () {
    topnavbar();

    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    startingBookId = parseInt(urlParams.get("centerbookid"));
    windowSize = parseInt(urlParams.get("windowsize"));
    if (isNaN(startingBookId)) {
        startingBookId = 2;
    }
    if (isNaN(windowSize)) {
        windowSize = 12;
    }
    console.log(startingBookId);

    const endpointUrl = baseApiUrl + "/complete_records_window";
    // GET with 2 parameeters /BOOKID/WINDOWSIZE
    const url = endpointUrl + "/" + startingBookId + "/" + windowSize;
    $.getJSON(url, function (data) {
        minCarouselBookId = data[0]['book']['data'][0][0];
        maxCarouselBookId = data[windowSize - 1]['book']['data'][0][0];
        for (var bookIdx = 0; bookIdx < windowSize; bookIdx++) {
            const bookObj = data[bookIdx]['book'];
            const readObj = data[bookIdx]['reads'];
            const tagObj = data[bookIdx]['tags'];
            const imgObj = data[bookIdx]['img'];
            var bookString = listItems(bookObj, readObj, tagObj, imgObj);
            $("#card-deck").append(bookString);
        }
        //console.log(minCarouselBookId, maxCarouselBookId, url);
        swiper.init(); // Initialize Swiper after content is ready
    });
});

function listItems(bookObj, readObj, tagObj, imgObj) {
    var imgUrl = resourceUrl + "/default.webp";
    //console.log(imgObj['data'][0]);
    if (imgObj['data'][0].length > 0) {
        imgUrl = imgObj['data'][0][0];
    }

    let bookString = "\n<li class=\"card-item swiper-slide\">\n" +
        " <a href=\"#\" class=\"card-link\">\n";
    bookString += "  <div class=\"book-record\">\n";
    bookString += "    <img src=\"" + imgUrl + "\" class=\"card-image\">\n";
    bookString += "    <div class=\"badge\">" + bookObj['data'][0][1] + "</div>\n";
    let fieldsList = [2, 3, 4, 12, 0, 5, 6, 7, 11, 9];
    for (const i of fieldsList) {
        bookString += "    <span class='field-title'>" + bookObj['header'][i] + ":</span> " + bookObj['data'][0][i] + "</br>\n";
    }
    if (readObj['data'].length > 0) {
        for (var i = 1; i < readObj['header'].length; i++) {
            bookString += "</br>    <span class='field-title'>Reading Notes:</span> " + readObj['data'][0][i] + "</br>\n";
        }
    }
    bookString += "</br>    <span class='field-title'>" + tagObj['header'][0] + ":</span> " + tagObj['data'][0].join(", ") + "</br>\n";
    bookString += "    <button class=\"card-button\"><i class=\"fa-solid fa-arrow-right\"></i></button>\n";
    bookString += "  </div>\n  </a>\n</li>\n";
    //console.log(bookString);
    return bookString;
}

const swiper = new Swiper('.card-wrapper', {
    init: false,
    loop: false,
    speed: 700,
    spaceBetween: 30,
    direction: 'horizontal',

    // If we need pagination
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
        dynamicBullets: true,
    },

    // Navigation arrows
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },

    breakpoints: {
        0: {
            slidesPerView: 1
        },
        768: {
            slidesPerView: 2
        },
        1024: {
            slidesPerView: 3
        },
    }
});

swiper.on('reachBeginning', function () {
    const endpointUrl = baseApiUrl + "/complete_record";
    const direction = "previous";
    const url = endpointUrl + "/" + minCarouselBookId + "/" + direction;
    //console.log(minCarouselBookId, maxCarouselBookId, url);
    $.getJSON(url, function (data) {
        minCarouselBookId = data['book']['data'][0][0];
        const bookObj = data['book'];
        const readObj = data['reads'];
        const tagObj = data['tags'];
        const imgObj = data['img'];
        swiper.prependSlide(listItems(bookObj, readObj, tagObj, imgObj));
        swiper.update(); // Update Swiper after adding new slides
    });
});

swiper.on('reachEnd', function () {
    const endpointUrl = baseApiUrl + "/complete_record";
    const direction = "next";
    const url = endpointUrl + "/" + maxCarouselBookId + "/" + direction;
    console.log(minCarouselBookId, maxCarouselBookId, url);
    $.getJSON(url, function (data) {
        maxCarouselBookId = data['book']['data'][0][0];
        const bookObj = data['book'];
        const readObj = data['reads'];
        const tagObj = data['tags'];
        const imgObj = data['img'];
        swiper.appendSlide(listItems(bookObj, readObj, tagObj, imgObj));
        swiper.update(); // Update Swiper after adding new slides
    });
});
