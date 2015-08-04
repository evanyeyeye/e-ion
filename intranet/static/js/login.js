$(document).ready(function() {
    /* Input */
    var $username = $("input[name=username]");
    var $password = $("input[name=password]");
    if(!$username.hasClass("error") && $password.hasClass("error")) {
        $password.focus();
    } else {
        $username.focus();
    }

    $(".logo").click(function() {
        location.href = (window.osearch ? "/?"+window.osearch.substring(0, window.osearch.length-1) : "/");
    });

    $("#revision").click(function(e) {
        if (e.altKey) {
            location.href = $(this).attr("data-github-url");
        }
    });

});