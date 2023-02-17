$(function () {
    $(".switch").on("mouseover", upimg);
    $(".switch").on("mouseout", downimg);
    // #表单验证
    $("input[name='username']").on('blur', function () {
        if ($.trim($(this).val()) == '') {
            $(this).parent().next().addClass("err_tips_err");
        } else {
            $(this).parent().next().removeClass("err_tips_err");
        }
    });
    $("input[name='username']").on('focus', function () {
        $(this).parent().next().removeClass("err_tips_err");
    });
    // 密码
    $("input[name='password']").on("blur", function () {
        if ($.trim($(this).val()) == "") {
            $(".password_group").children().not(":eq(0)").hide();
            $(".password_group").children().eq(0).fadeToggle();
            $(".password_group").children().eq(0).addClass("err_tips_err");

        }
    })
    $("input[name='password']").on("focus", function () {
        if ($.trim($(this).val()) == "") {
            $(".password_group").children().eq(0).css("display","none")
            $(".password_group").children().not(":eq(0)").fadeToggle();
        }
    })
})

function downimg() {
    $(".language img").attr("src", "images/down.png");
    $(".switch ul").css("display", "none");
    $(".language").css("color", "#888");
}

function upimg() {
    $(".language img").attr("src", "images/up.png");
    $(".switch ul").css("display", "block");
    $(".language").css("color", "#000");
}