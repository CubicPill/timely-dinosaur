$(document).ready(function () {
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
            success: function (data) {
                console.log(data);
            },

            contentType: "application/json"
        });
        input.val("");
    });
});

function updateSearchResults(data) {
    if (!data.ok) {
        return;
    }

}
