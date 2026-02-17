// Handle form submission
let form = document.forms.add_book_estimate;
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
var book_id = urlParams.get("book_id");
window.addEventListener('DOMContentLoaded', function() {
    topnavbar();
})

form.addEventListener('submit', function(event) {
    event.preventDefault(); // prevent page reload
    console.log("submit called...");
    // get form values
    var start_date = document.forms["add_book_estimate"]["start_date"].value;
    var readable_pages = document.forms["add_book_estimate"]["readable_pages"].value;
    // get form values
    console.log(start_date, readable_pages, book_id);
    // submit form data
    var xhr = new XMLHttpRequest();
    var url = baseApiUrl + "/add_book_estimate/" + book_id;
    url += "/" + readable_pages + "/" + start_date;
    console.log(url);
    xhr.open("PUT", url, true);
    xhr.setRequestHeader('x-api-key', apiKey);
    xhr.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var resp = JSON.parse(xhr.responseText);
            console.log(resp);
            if ("error" in resp) {
                alert("Error: " + resp.error);
            } else {
                var book_id = resp.add_book_estimate.BookId;
                alert("Entry added successfully!\n Book ID=" + book_id);
            }
            window.location.href = "./books_detail.html?bookid=" + book_id.toString();
        }
        // else {
        //     alert("readyState: " + this.readyState + " status: " + this.status);
        // }
    }
    xhr.send();
    return false;
})
