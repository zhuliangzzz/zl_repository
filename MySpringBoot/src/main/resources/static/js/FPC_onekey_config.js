var pagecount = 13;              // 每页数据量
var tabledata = []             // 数据总数
var totalPage = undefined   //总页数
var currentPage = 1         //当前页
$(function () {
    // # 获取所有子脚本
    $.ajax({
        url: "/script/getOneKeyScripts",
        type: "get",
        success: function (callback) {
            tabledata = callback;
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
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-primary active">' + i + '</a></li>'
                    } else {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-primary">' + i + '</a></li>'
                    }
                }
            }else{
                for (var i = 1; i <= totalPage; i++) {
                    if (i === 1) {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-primary active">' + i + '</a></li>'
                    } else {
                        pager_btn += '<li><a href="javascript:showpage(' + i + ')" class="btn btn-primary">' + i + '</a></li>'
                    }
                }
            }

            $("#pager_ul li:first").after(pager_btn);
            showpage(currentPage);
        } // end
    });
});

function showpage(pagenum) {
    $("#datatable tbody").empty();
    currentPage = pagenum;
    for (var i = 0; i < tabledata.length; i++) {
        if(tabledata.length <= pagecount){
            var info_replace = tabledata[i].scriptinfo.replace(/\\n/g, "<br>");
            $("#datatable tbody").append("<tr><td>" + tabledata[i].adddate + "</td><td>"
                + tabledata[i].scriptname + "</td><td>" + tabledata[i].scriptlevel + "</td><td>"
                + tabledata[i].scriptpath + "</td><td>" + tabledata[i].scriptkey + "</td><td>"
                + info_replace + "</td><td>" + tabledata[i].scriptclass + "</td><td>"
                + tabledata[i].testuser + "</td></tr>");
        }else{
            if ((pagenum - 1) * pagecount <= i && i < pagenum * pagecount) {
                var info_replace = tabledata[i].scriptinfo.replace(/\\n/g, "<br>");
                $("#datatable tbody").append("<tr><td>" + tabledata[i].adddate + "</td><td>"
                    + tabledata[i].scriptname + "</td><td>" + tabledata[i].scriptlevel + "</td><td>"
                    + tabledata[i].scriptpath + "</td><td>" + tabledata[i].scriptkey + "</td><td>"
                    + info_replace + "</td><td>" + tabledata[i].scriptclass + "</td><td>"
                    + tabledata[i].testuser + "</td></tr>");
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

