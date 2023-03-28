var user;
// const bloggerlist = $("#hiddenBloggerList").val();
// console.log(typeof bloggerlist)
// bloggerlist.forEach(function (v, i, a) {
//     var o = javaStrToJson(v);
//     console.log(o);
// });

var cur_page = Number($("#currentPage").val());
var bloggerPages = Number($("#bloggerPages").val());
$(".dropdown>a").append('<span class=\"caret\"></span>');
$(".pagination li").eq(cur_page).addClass("active");
if(cur_page==1){
    $("a.prev").attr("disabled",true);
}
if(cur_page == bloggerPages){
    $("a.next").attr("disabled",true);
}


$(function () {
    $(".delUserBtn").on("click", removeUser);
    $(".editUserBtn").on("click", editUser);
    $(".addUserBtn").on("click", addUser);
    $("#exit_link").click(logout);
    $("a.page").on("click",skipPage);
    $("a.prev").bind("click",prePage);
    $("a.next").bind("click",nextPage);
});

//删除
function removeUser() {
    user = $(this).parent().parent().attr("user");
    user = javaStrToJson(user);
    $.ajax({
        url: "/blogger/del",
        data: {
            id: user.id
        },
        type: "json",
        method: "post",
        success: function (res) {
            location.reload()
        }
    })
}

//新增
function addUser() {
    var name = $("#blog_name").val();
    var pwd = $("#blog_pwd").val();
    $.ajax({
        url:"/blogger/add",
        data:{
            name:name,
            pass:pwd
        },
        type:"json",
        method:"post",
        success:function(res){
            console.log(res)
            if(res === -1){
                alert("用户" + name + "已存在");
            }else if(res===0){
                alert("用户" + name + "添加失败");
            }else{
                location.reload();
            }
        }
    })

}

//编辑
function editUser() {
    user = $(this).parent().parent().attr("user");
    user = javaStrToJson(user);
    $("#name").val(user.name)
    $("#pwd").val(user.pass)
}

function editSave() {
    // var user = $(this).parent().parent().attr("user");
    var name = $("#name").val();
    var pass = $("#pwd").val();
    if (pass === user.pass) {
        return;
    } else if (pass.trim() === "") {
        alert("密码不能为空");
        return;
    }
    $.ajax({
        url: "/blogger/edit",
        data: {
            name: name,
            pass: pass
        },
        type: "json",
        method: "post",
        success: function (res) {
            location.reload()
        }
    })
}
//换页
function skipPage(){
    // $.ajax({
    //     url: "/blogger/getBloggerOnPage",
    //     data: {
    //         page: $(this).text()
    //     },
    //     type: "json",
    //     method: "post",
    //     success: function (res) {
    //         location.href =
    //     }
    // })
    cur_page = $(this).text();
    location.href="/blogger/getBloggerOnPage?page="+ cur_page;
}
function prePage(){
    cur_page--;
    if(cur_page < 1){
        cur_page=1;
        $("a.prev").attr("disabled",true);
        return;
    }
    location.href="/blogger/getBloggerOnPage?page="+ cur_page;
}
function nextPage() {
    cur_page++;
    if(cur_page > bloggerPages ){
        cur_page=bloggerPages;
        $("a.next").attr("disabled",true);
        return;
    }
    location.href="/blogger/getBloggerOnPage?page="+ cur_page;
}


function logout() {
    location.href="/blogger/logout";

}

//把java对象解析为json
function javaStrToJson(str) {
    var content = str.replace(/[,']/g, '').match(/{(.*)}/)[1].split(" ");
    var jsonArr = []
    content.forEach(function (v, i, a) {
        jsonArr.push('"' + v.split("=")[0] + '"' + ':' + '"' + v.split("=")[1] + '"');
    });
    return JSON.parse('{' + jsonArr.join() + '}');
}