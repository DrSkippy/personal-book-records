var bookTitle = "Book Title";
var readReadDate = "Read Date";
var bookAuthor = "Book Author";
var bookNote = "Book Note";
var readReadNote = "Read Note";
var idArrayIndex = 0;
var idArraySubIndex = 0;
var subArraySize = 0;

$(document).ready(function () {
    topnavbar();
    $.ajaxSetup({async: false});  // suppress async so the summary row is always at the bottom

    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    // ...&idArray=1604&idArray=1605&idArray=1696
    idArray = urlParams.getAll("idArray")[0].split(",");
    //console.log(idArray);
    populateFields();
});

function populateFields() {
    bookCollectionID = idArray[idArrayIndex];
    const urlRead = baseApiUrl + "/status_read/" + bookCollectionID;
    $.getJSON(urlRead, function (data) {
        var obj = data['data'];
        // possibly more than one read record per book
        // use idArraySubIndex
        subArraySize = obj.length;
        if (idArraySubIndex < 0) {
            // last element in the subArray
            // this happens when navigating backward
            idArraySubIndex = subArraySize - 1;
        }
        readReadDate = obj[idArraySubIndex][1];
        readReadNote = obj[idArraySubIndex][2];
    });

    var urlBook = baseApiUrl + "/books_search?BookCollectionID=" + bookCollectionID;
    $.getJSON(urlBook, function (data) {
        var obj = data['data'];
        bookTitle = obj[0][1];
        bookAuthor = obj[0][2];
        bookNote = obj[0][9];
    });

    document.getElementById('bookBookCollectionIDField').innerHTML = bookCollectionID;
    document.getElementById('readBookCollectionIDField').innerHTML = bookCollectionID;
    document.getElementById('bookTitleField').innerHTML = bookTitle;
    document.getElementById('bookAuthorField').innerHTML = bookAuthor;
    document.getElementById('readReadDateField').innerHTML = '<input type="text" id="bookReadDateValue" ' + 
        'size=15 value=' + readReadDate + '></input>';
    document.getElementById('bookNoteField').innerHTML = '<textarea id="bookNoteValue" ' +
        'cols="45" rows="5">' + bookNote + '</textarea>';
    document.getElementById('readReadNoteField').innerHTML = '<textarea id="readReadNoteValue" ' +
        'cols="45" rows="5">' + readReadNote + '</textarea>';
}

function navigate(direction) {
    if (direction == 1) {
        // moving forward
        if (idArraySubIndex < subArraySize - 1) {
            // increment sub index, leave index alone
            idArraySubIndex += 1;
        } else {
            // increment index, set sub index to first element
            idArraySubIndex = 0;
            idArrayIndex += 1;
            if (idArrayIndex > idArray.length - 1) {
                // wrap index if necessary
                idArrayIndex = 0;
            }
        }
    } else {
        // moving backward
        if (idArraySubIndex > 0) {
            // decrement sub index, leave index alone
            idArraySubIndex -= 1;
        } else {
            // -1 is last element in previous array, see above
            idArraySubIndex = -1;
            idArrayIndex -= 1;
            if (idArrayIndex < 0) {
                // wrap index if necessary
                idArrayIndex = idArray.length - 1;
            }
        }
    }
    populateFields();
    console.log(idArrayIndex);
    console.log(idArraySubIndex);
}

function update_note() {
    readNote = document.getElementById("readReadNoteValue").value
    readDate = document.getElementById("bookReadDateValue").value
    bookNote = document.getElementById("bookNoteValue").value

    const dataRead = JSON.stringify({
        "BookCollectionID": bookCollectionID,
        "ReadDate": readDate,
        "ReadNote": readNote
    });
    const dataBook = JSON.stringify({
        "BookCollectionID": bookCollectionID,
        "Note": bookNote
    });
    console.log(dataRead);
    console.log(dataBook);

    const urlBook = baseApiUrl + "/update_book_note_status";
    const urlRead = baseApiUrl + "/update_edit_read_note";

    // Post the data
    xhr = new XMLHttpRequest();
    xhr.open("POST", urlBook, false);
    xhr.setRequestHeader("Content-Type", "application/json; charset=UTF-8");
    xhr.setRequestHeader('x-api-key', apiKey);
    xhr.send(dataBook);
    xhr = new XMLHttpRequest();
    xhr.open("POST", urlRead, false);
    xhr.setRequestHeader("Content-Type", "application/json; charset=UTF-8");
    xhr.setRequestHeader('x-api-key', apiKey);
    xhr.send(dataRead);
    navigate(1);
    console.log(xhr.response);
}
