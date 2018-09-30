const colors = [
    "#42a5f5",
    "#3f51b5",
    "#5e35b1",
    "#ab47bc",
    "#f06292",
    "#ef9a9a",
    "#f57f17",
    "#afb42b",
    "#7cb342",
    "#4caf50",
    "#00897b",
    "#4dd0e1",
    "#b39ddb",
    "#b2dfdb",
    "#546e7a",
    "#9e9e9e",
    "#8d6e63"
];
let colorsAvailable = colors;

$(document).ready(function () {
    initPage();
    window.TDSeletions = [];
    window.timeTable = [];
});

function initPage() {

    $("#query-btn").click(onClickSearchBtn);
    loadSavedResults();
    $("#save-btn").click(saveResult());
    // $("#toggle-week").bootstrapToggle({
    //     on: "单周",
    //     off: "双周",
    //     onstyle: "primary",
    //     offstyle: "primary"
    // });
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
    if (data["subName"] === null) {
        data["subName"] = "";
    }
    if (data["classroom"] === null) {
        data["classroom"] = "";
    }
    if (data["instructor"] === null) {
        data["instructor"] = ""
    }
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
        $.ajax({
            url: "/schedule/" + data["jx0404id"],
            type: "GET",
            success: function (schedule) {
                addCourseToTable(data, schedule["data"]);
                addToList(data);
                window.TDSeletions.push(data["jx0404id"]);
            }
        });

    });
    return element;
}

function pickColor() {
    if (colorsAvailable.length === 0) {
        colorsAvailable = colors;
    }
    let color = colorsAvailable[Math.floor(Math.random() * colorsAvailable.length)];
    colorsAvailable.splice(colorsAvailable.indexOf(color), 1);
    return color;
}

function addCourseToTable(data, schedules) {
    let color = pickColor();
    for (let i = 0; i < schedules.length; ++i) {
        let schedule = schedules[i];
        let time = schedule["time"].split("-");
        let duration = parseInt(time[1]) - parseInt(time[0]) + 1;
        if (schedule["classroom"] === null) {
            schedule["classroom"] = "";
        }
        let courseDiv = $('<div>' +
            data["name"] + "<br>" +
            schedule["classroom"] + "<br>" +
            schedule["weekShort"] + "周" +
            "</div>");
        courseDiv.addClass("course");
        courseDiv.addClass("course" + data["jx0404id"]);
        courseDiv.addClass("course" + duration);
        courseDiv.css("background", color);
        $("#class" + schedule["dayOfWeek"] + "-" + time[0]).append(courseDiv);

        $(courseDiv).popover({
            container: "body",
            trigger: "hover",
            placement: "left",
            html: true,
            content: "授课教师: " + data["instructor"]
        });
    }

}

function removeCourse(jx0404id) {
    window.TDSeletions.splice(window.TDSeletions.indexOf(jx0404id), 1);
    $("#tr" + jx0404id).remove();
    $("#tbl-main").find("div.course" + jx0404id).remove();
}

function addToList(data) {
    if (data["prerequisite"] === null) {
        data["prerequisite"] = "无";
    }
    if (data["classroom"] === null) {
        data["classroom"] = "";
    }
    let insertedRow = $(" <tr id='tr" + data["jx0404id"] + "'>" +
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
        removeCourse(data["jx0404id"]);
    });
    $('#tbl-selected').find('tr:last').after(insertedRow);

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


function isCourseOverlap(schedules) {

}