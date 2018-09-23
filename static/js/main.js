$(document).ready(function () {
    initPage();
    window.TDSeletions = [];
});

function initPage() {
    $("#query-btn").click(onClickSearchBtn);
    loadSavedResults();

}

function onClickSearchBtn() {
    console.log('search!');
    var queryInput = $("#query-txt").val();
    if (!queryInput) {
        return;
    }
    var queryType = $("#query-type").val();
    $.ajax({
        type: "POST",
        url: "/search",
        data: JSON.stringify({
            query: queryInput,
            queryType: queryType

        }),
        success: onSearchSuccess,
        contentType: "application/json"
    });
}

function saveResult() {
    console.log('Save result');

}

function table(row, column, content) {

}

function generateCourseCard(data) {

    var element = $("<li class='result'>" +
        "<p>" +
        data["courseNo"] + " " + data["name"] +
        "</p>" +
        "<p>" +
        data["subName"] +
        "</p>" +
        "<p>" +
        data["instructor"] +
        "</p>" +
        "<p>" +
        data["classroom"] +
        "</p>" +
        "<p>" +
        data["time"] +
        "</p>" +
        "</li>");
    element.click(function () {
        addToTable(data);
        addToList(data);
        window.TDSeletions.push(data["jx0404id"]);
    });
    return element;
}

function addToTable(data) {

}

function addToList(data) {

}

function onSearchSuccess(data) {
    var resultList = $("#result-list");
    resultList.empty();
    if (!data.ok) {
        console.error('API return: Not OK');
        return;
    }
    for (var i = 0; i < data['data'].length; ++i) {
        resultList.append(generateCourseCard(data['data'][i]));
    }
}

function loadSavedResults() {
    $.ajax({
        type: "GET",
        url: "/save",
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