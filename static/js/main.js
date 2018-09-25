$(document).ready(function () {
    initPage();
    window.TDSeletions = [];
});

function initPage() {
    $("#query-btn").click(onClickSearchBtn);
    loadSavedResults();

}

function onClickSearchBtn() {
    let queryInput = $("#query-txt").val();
    if (!queryInput) {
        return;
    }
    let queryType = $("#query-type").val();
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
    $.ajax({
        type: "POST",
        url: "/save",
        data: JSON.stringify({
            id: window.TDSeletions
        })
    });
}

function modifyCourseTable(row, column, content) {

}

function generateCourseCard(data) {

    let element = $("<li class='result'>" +
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
        if (window.TDSeletions.indexOf(data["jx0404id"]) >= 0) {
            return;
        }
        addToTable(data);
        addToList(data);
        window.TDSeletions.push(data["jx0404id"]);
    });
    return element;
}

function addToTable(data) {
}

function addToList(data) {
    let insertedRow = $(" <tr>" +
        "                    <td>" + data["jx0404id"] + "</td>" +
        "                    <td>" + data["courseNo"] + "</td>" +
        "                    <td>" + data["name"] + "[" + data["subName"] + "]</td>" +
        "                    <td>" + data["instructor"].replace(",", "<br>") + "</td>" +
        "                    <td>" + data["time"].replace(",", "<br>") + "</td>" +
        "                    <td>" + data["classroom"].replace(",", "<br>") + "</td>" +
        "                    <td>" + data["prerequisite"] + "</td>" +
        "                    <td>" + data["credit"] + "</td>" +
        "                </tr>");
    $('#tbl-selected tr:last').after(insertedRow);
}

function onSearchSuccess(data) {
    let resultList = $("#result-list");
    resultList.empty();
    if (!data.ok) {
        console.error('API return: Not OK');
        return;
    }
    for (let i = 0; i < data['data'].length; ++i) {
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