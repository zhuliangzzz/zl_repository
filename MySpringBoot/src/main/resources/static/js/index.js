// var user;
// const bloggerlist = $("#hiddenBloggerList").val();
// console.log(typeof bloggerlist)
// bloggerlist.forEach(function (v, i, a) {
//     var o = javaStrToJson(v);
//     console.log(o);
// });
var way = true; //查询方式 全部查询、按料号名查询   默认为全部查询
var cur_page = Number($("#currentPage").val());
var bloggerPages = Number($("#bloggerPages").val());

$(function () {
    pager();
    // $(".showPaper").bind("click", showPaper)
    // $("#exit_link").bind("click", logout);
    // $("#searchBtn").bind("click", search)
    // $("a.page").bind("click", skipPage);
    // $("a.prev").bind("click", prePage);
    // $("a.next").bind("click", nextPage);
    $(document).on('click', ".showPaper", showPaper)
    $(document).on('click', "#exit_link", logout)
    $(document).on('click', "#searchBtn", search)
    $(document).on('click', "a.page", skipPage)
    $(document).on('click', "a.prev", prePage)
    $(document).on('click', "a.next", nextPage)
});

function pager() {
// $(".dropdown>a").append('<span class=\"caret\"></span>');
    $(".pagination li").eq(cur_page).addClass("active");
    if (cur_page == 1) {
        $("a.prev").attr("disabled", true);
    }
    if (cur_page == bloggerPages) {
        $("a.next").attr("disabled", true);
    }
}

$(".dropdown>a").append('<span class=\"caret\"></span>');
$(function () {
    $("#exit_link").click(logout);
});

//换页
function skipPage() {
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
    if (cur_page == 1) {
        $("a.prev").attr("disabled", true);
    }
    if (cur_page == bloggerPages) {
        $("a.next").attr("disabled", true);
    }

    if (way) {
        location.href = "/film/getFilmOnPage?page=" + cur_page;
    } else {
        // location.href="/film/searchFilmOnPage?name=" +  $("#searchInput").val().trim() + "&page="+ cur_page;
        $.ajax({
            url: "/film/searchFilmOnPage",
            data: {
                name: $("#searchInput").val().trim(),
                page: cur_page
            },
            type: "json",
            method: "post",
            success: function (res) {
                $("tbody").empty();
                $("#pager ul").empty();
                console.log(res.dataPages);
                console.log(res.currentPage);
                console.log(res.datalist);
                bloggerPages = res.dataPages;
                currentPage = res.currentPage;
                var data = "";
                for (var i = 0; i < res.datalist.length; i++) {
                    data += '<tr class="row">' +
                        '<td class="col-md-1">' + res.datalist[i].id + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].inplanJob + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].face + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].checkNo + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].checkProjectName + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].standardValue + '</td>' +
                        '<td class="col-md-2">' + res.datalist[i].notes + '</td>' +
                        '<td class="col-md-2">' + res.datalist[i].imageName + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].oprTime + '</td>' +
                        '<td class="col-md-1"><a class="btn btn-primary showPaper" data-toggle="modal" name="' + res.datalist[i].imageName + '"data-target="#myModal">查看图纸</a>' +
                        '</td>' +
                        '</tr>'
                }
                $("tbody").append(data);
                var count = res.dataPages;
                if (count > 10) {
                    count = 10;
                }
                $("#cp").text(currentPage);
                $("#tp").text(bloggerPages);
                $("#pager ul").append('<li><a class="prev btn btn-default">&laquo;</a></li>');
                for (var i = 1; i <= count; i++) {
                    $("#pager ul").append('<li><a class="page btn">' + i + '</a></li>')
                }
                $("#pager ul").append('<li><a class="next btn btn-default">&raquo;</a></li>');
                pager();
            }
        })
    }

}

function prePage() {
    cur_page--;
    if (cur_page < 1) {
        cur_page = 1;
        $("a.prev").attr("disabled", true);
        return;
    }

    if (way) {
        location.href = "/film/getFilmOnPage?page=" + cur_page;
    } else {
        // location.href = "/film/searchFilmOnPage?name=" + $("#searchInput").val().trim() + "&page=" + cur_page;
        $.ajax({
            url: "/film/searchFilmOnPage",
            data: {
                name: $("#searchInput").val().trim(),
                page: cur_page
            },
            type: "json",
            method: "post",
            success: function (res) {
                $("tbody").empty();
                $("#pager ul").empty();
                console.log(res.dataPages);
                console.log(res.currentPage);
                console.log(res.datalist);
                bloggerPages = res.dataPages;
                currentPage = res.currentPage;
                var data = "";
                for (var i = 0; i < res.datalist.length; i++) {
                    data += '<tr class="row">' +
                        '<td class="col-md-1">' + res.datalist[i].id + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].inplanJob + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].face + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].checkNo + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].checkProjectName + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].standardValue + '</td>' +
                        '<td class="col-md-2">' + res.datalist[i].notes + '</td>' +
                        '<td class="col-md-2">' + res.datalist[i].imageName + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].oprTime + '</td>' +
                        '<td class="col-md-1"><a class="btn btn-primary showPaper" data-toggle="modal" name="' + res.datalist[i].imageName + '" data-target="#myModal">查看图纸</a>' +
                        '</td>' +
                        '</tr>'
                }
                $("tbody").append(data);
                var count = res.dataPages;
                if (count > 10) {
                    count = 10;
                }
                $("#cp").text(currentPage);
                $("#tp").text(bloggerPages);
                $("#pager ul").append('<li><a class="prev btn btn-default">&laquo;</a></li>');
                for (var i = 1; i <= count; i++) {
                    $("#pager ul").append('<li><a class="page btn">' + i + '</a></li>')
                }
                $("#pager ul").append('<li><a class="next btn btn-default">&raquo;</a></li>');
                pager();
            }
        })
    }
}

function nextPage() {
    cur_page++;
    if (cur_page > bloggerPages) {
        cur_page = bloggerPages;
        $("a.next").attr("disabled", true);
        return;
    }
    if (way) {
        location.href = "/film/getFilmOnPage?page=" + cur_page;
    } else {
        // location.href = "/film/searchFilmOnPage?name=" + $("#searchInput").val().trim() + "&page=" + cur_page;
        $.ajax({
            url: "/film/searchFilmOnPage",
            data: {
                name: $("#searchInput").val().trim(),
                page: cur_page
            },
            type: "json",
            method: "post",
            success: function (res) {
                $("tbody").empty();
                $("#pager ul").empty();
                console.log(res.dataPages);
                console.log(res.currentPage);
                console.log(res.datalist);
                bloggerPages = res.dataPages;
                currentPage = res.currentPage;
                var data = "";
                for (var i = 0; i < res.datalist.length; i++) {
                    data += '<tr class="row">' +
                        '<td class="col-md-1">' + res.datalist[i].id + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].inplanJob + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].face + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].checkNo + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].checkProjectName + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].standardValue + '</td>' +
                        '<td class="col-md-2">' + res.datalist[i].notes + '</td>' +
                        '<td class="col-md-2">' + res.datalist[i].imageName + '</td>' +
                        '<td class="col-md-1">' + res.datalist[i].oprTime + '</td>' +
                        '<td class="col-md-1"><a class="btn btn-primary showPaper" data-toggle="modal" name="' + res.datalist[i].imageName + '" data-target="#myModal">查看图纸</a>' +
                        '</td>' +
                        '</tr>'
                }
                $("tbody").append(data);
                var count = res.dataPages;
                if (count > 10) {
                    count = 10;
                }
                $("#cp").text(currentPage);
                $("#tp").text(bloggerPages);
                $("#pager ul").append('<li><a class="prev btn btn-default">&laquo;</a></li>');
                for (var i = 1; i <= count; i++) {
                    $("#pager ul").append('<li><a class="page btn">' + i + '</a></li>')
                }
                $("#pager ul").append('<li><a class="next btn btn-default">&raquo;</a></li>');
                pager();
            }
        })
    }
}

function showPaper() {
    // alert($(this).attr("name"));
    var image_name = $(this).attr("name");
    //判断文件是否存在
    $.ajax({
        url: "",
        type: 'HEAD',
        async: false,      //取消ajax的异步实现
        success: function () {
            // 文件存在
            $("embed").attr("src", "/pdf/" + image_name);
        },
        error: function () {
            // 文件不存在
            alert("文件不存在！");
        }
    });
    $("embed").attr("src", "/pdf/HI31828AISX_L7_20220421105729.pdf");

}

function search() {

    var searchVal = $("#searchInput").val();
    if (searchVal.trim() === "") {
        way = true;
    } else {
        way = false;
    }
    cur_page = 1;
    if (way) {
        location.href = "/film/getFilmOnPage?page=" + cur_page;
    } else {
        // location.href = "/film/searchFilmOnPage?name=" + searchVal.trim() + "&page=" + cur_page;
        $.ajax({
            url: "/film/searchFilmOnPage",
            data: {
                name: $("#searchInput").val().trim(),
                page: cur_page
            },
            type: "json",
            method: "post",
            success: function (res) {
                $("tbody").empty();
                $("#pager ul").empty();
                console.log(res.dataPages);
                console.log(res.currentPage);
                console.log(res.datalist);
                bloggerPages = res.dataPages;
                currentPage = res.currentPage;
                var data = "";
                if (res.datalist) {
                    for (var i = 0; i < res.datalist.length; i++) {
                        data += '<tr class="row">' +
                            '<td class="col-md-1">' + res.datalist[i].id + '</td>' +
                            '<td class="col-md-1">' + res.datalist[i].inplanJob + '</td>' +
                            '<td class="col-md-1">' + res.datalist[i].face + '</td>' +
                            '<td class="col-md-1">' + res.datalist[i].checkNo + '</td>' +
                            '<td class="col-md-1">' + res.datalist[i].checkProjectName + '</td>' +
                            '<td class="col-md-1">' + res.datalist[i].standardValue + '</td>' +
                            '<td class="col-md-2">' + res.datalist[i].notes + '</td>' +
                            '<td class="col-md-2">' + res.datalist[i].imageName + '</td>' +
                            '<td class="col-md-1">' + res.datalist[i].oprTime + '</td>' +
                            '<td class="col-md-1"><a class="btn btn-primary showPaper" data-toggle="modal" name="' + res.datalist[i].imageName + '" data-target="#myModal">查看图纸</a>' +
                            '</td>' +
                            '</tr>'
                    }
                    $("tbody").append(data);
                    var count = res.dataPages;
                    if (count > 10) {
                        count = 10;
                    }
                    $("#cp").text(currentPage);
                    $("#tp").text(bloggerPages);
                    $("#pager ul").append('<li><a class="prev btn btn-default">&laquo;</a></li>');
                    for (var i = 1; i <= count; i++) {
                        $("#pager ul").append('<li><a class="page btn">' + i + '</a></li>')
                    }
                    $("#pager ul").append('<li><a class="next btn btn-default">&raquo;</a></li>');
                    pager();
                    $("#pager").children('a').show();
                } else {
                    $("tbody").append('<tr class="row"><td colspan="10">无数据</td></tr>');
                    $("#pager").children('a').hide();
                }
            }
        })
    }
}

function logout() {
    location.href = "/blogger/logout";
}