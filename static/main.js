$(document).ready(function () {
    initPage();
});

function initPage() {
    $("#query-btn").click(function () {
        console.log('search!');
        let input = $("#query-txt");
        if (!input.val()) {
            return;
        }
        $.ajax({
            type: "POST",
            url: "/search",
            data: JSON.stringify({
                query: input.val()
            }),
            success: onSearchSuccess,
            contentType: "application/json"
        });
        input.val("");
    });
    loadSavedResults();

}

function saveResult() {
    console.log('Save result');

}

function table(row, column, content) {

}

function onSearchSuccess(data) {
    if (!data.ok) {
        console.error('API return: Not OK');
        return;
    }
    console.log(data);
}

function loadSavedResults() {
    $.ajax({
        type: "GET",
        url: "/load",
        success: function (data) {
            console.log(data);
        },

        contentType: "application/json"
    });
}

function showSearchResults(data) {

}

function isCourseOverlap() {

}