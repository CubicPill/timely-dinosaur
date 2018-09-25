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
        addCourseToTable(data);
        addToList(data);
        window.TDSeletions.push(data["jx0404id"]);
    });
    return element;
}


function modifyCourseTable(row, column, content) {

}

function addCourseToTable(data, schedule) {

}

function addToList(data) {

    let insertedRow = $(" <tr>" +
        "                    <td>" + data["jx0404id"] + "</td>" +
        "                    <td>" + data["courseNo"] + "</td>" +
        "                    <td>" + data["name"] + "<br>[" + data["subName"] + "]</td>" +
        "                    <td>" + data["instructor"].split(",").join("<br>") + "</td>" +
        "                    <td>" + data["time"].split("节,").join("节<br>") + "</td>" +
        "                    <td>" + data["classroom"].split(",").join("<br>") + "</td>" +
        "                    <td>" + data["prerequisite"].split(" ").join("<br>") + "</td>" +
        "                    <td>" + data["credit"] + "</td>" +
        "                    <td><button class='btn btn-warning'>删除</button></td>" +
        "                </tr>");
    let deleteButton = $(insertedRow).find("button");
    deleteButton.click(function () {
        alert(data["jx0404id"]);
    });
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
            
        },

        contentType: "application/json"
    });
}

function showSearchResults(data) {

}

function isCourseOverlap() {

}