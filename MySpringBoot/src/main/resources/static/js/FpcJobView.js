var pagecount = 20;              // 每页数据量
var tabledata = []             // 数据总数
var totalPage = undefined   //总页数
var currentPage = 1         //当前页
$(function () {
    $.ajax({
        url: '/script/getjobinfos',
        method: 'get',
        success: function (data) {
            tabledata = data;
            if (tabledata.length % pagecount) {
                totalPage = Math.ceil(tabledata.length / pagecount)
            } else {
                totalPage = tabledata.length / pagecount
            }
            var pager_btn = "";
            // # 最多显示五页
            if (totalPage > 5) {
                for (var i = 1; i <= 5; i++) {
                    if (i === 1) {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success active">' + i + '</a></li>'
                    } else {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success">' + i + '</a></li>'
                    }
                }
            } else {
                for (var i = 1; i <= totalPage; i++) {
                    if (i === 1) {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success active">' + i + '</a></li>'
                    } else {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success">' + i + '</a></li>'
                    }
                }
            }

            $("#pager_ul li:first").after(pager_btn);
            showpage(currentPage);
        }
    });
    //查询料号
    $("#search_btn").on("click", search)
});

function showpage(pagenum) {
    $("#table_content").empty();
    currentPage = pagenum;
    for (var i = 0; i < tabledata.length; i++) {
        if (tabledata.length <= pagecount) {
            var name = tabledata[i].jobname, code = tabledata[i].customerCode, color = tabledata[i].sm_color,
                time = tabledata[i].savetime;
            var trs = "<tr><td>" + name + "</td><td>" + code + "</td><td>" + color + "</td><td>" + time + "</td></tr>"
            $("#table_content").append(trs)
        } else {
            if ((pagenum - 1) * pagecount <= i && i < pagenum * pagecount) {
                var name = tabledata[i].jobname, code = tabledata[i].customerCode, color = tabledata[i].sm_color,
                    time = tabledata[i].savetime;
                var trs = "<tr><td>" + name + "</td><td>" + code + "</td><td>" + color + "</td><td>" + time + "</td></tr>"
                $("#table_content").append(trs)
            }
        }

    }
    $("#pager_ul a").removeClass('active');
    // $("#pager_ul a").addClass('active');
    // // this.addClass('active');
    // alert( $("#pager_ul a:eq(pagenum)"));
    $("#pager_ul a:eq(" + pagenum + ")").addClass("active");
    $("#pager span:eq(0)").text(currentPage);
    $("#pager span:eq(1)").text(totalPage);
}

function previousPage() {
    currentPage--;
    if (currentPage < 1) {
        currentPage = 1;
        return
    }
    showpage(currentPage);
}

function nextPage() {
    currentPage++;
    if (currentPage > totalPage) {
        currentPage = totalPage;
        return
    }
    showpage(currentPage);
}

function search() {
    var search_input = $("#search_input").val();
    $.ajax({
        url: '/script/getjobinfobyname',
        data: {
            "name": search_input
        },
        method: 'get',
        success: function (data) {
            tabledata = data;
            if (tabledata.length % pagecount) {
                totalPage = Math.ceil(tabledata.length / pagecount)
            } else {
                totalPage = tabledata.length / pagecount
            }

            var pager_btn = "";
            // # 最多显示五页
            if (totalPage > 5) {
                for (var i = 1; i <= 5; i++) {
                    if (i === 1) {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success active">' + i + '</a></li>'
                    } else {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success">' + i + '</a></li>'
                    }
                }
            } else {
                for (var i = 1; i <= totalPage; i++) {
                    if (i === 1) {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success active">' + i + '</a></li>'
                    } else {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-success">' + i + '</a></li>'
                    }
                }
            }
            // 移除中间的page
            var length = $("#pager_ul li").length;
            for (var i = 1; i < length-1; i++) {
                $("#pager_ul li:eq(1)").remove();
            }
            console.log(pager_btn)
            $("#pager_ul li:first").after(pager_btn);
            var currentPage = 1;
            showpage(currentPage);
        }
    });
}