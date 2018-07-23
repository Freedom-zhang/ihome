function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 点击退出按钮时执行的函数
function logout() {
    $.ajax({
        url: "/api/v1_0/session",
        type: "delete",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        dataType: "json",
        success: function (resp) {
            if (resp.errno == 0) {
                location.href = "/index.html";
            }
        }
    });
}

$(document).ready(function(){
    $.get("/api/v1_0/user", function(resp){
        // 用户未登录
        if (resp.errno == 4101) {
            location.href = "/login.html";
        }
        // 查询到了用户的信息
        else if (resp.errno == 0) {
            $("#user-name").html(resp.data.name);
            $("#user-mobile").html(resp.data.mobile);
            if (resp.data.avatar) {
                $("#user-avatar").attr("src", resp.data.avatar);
            }

        }
    }, "json");
})