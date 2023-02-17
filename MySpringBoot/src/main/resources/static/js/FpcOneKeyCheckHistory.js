var pagecount = 20;              // 每页数据量
var tabledata = []             // 数据总数
var totalPage = undefined   //总页数
var currentPage = 1         //当前页
$(function () {
    $.ajax({
        url: '/script/getOneKeyCheckHistory',
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
    $("#exportExcel").on("click",function () {
        alert(tabledata);
        $.ajax({
            url:"/excel/export2",
            method:'post',
            contentType: "application/json; charset=utf-8",
            // dataType:'json',
            // headers:{
            //     "Content-Type":"application/json"
            // },
            data: JSON.stringify(tabledata),
            // data: tabledata,
            success:function (callback) {

            }
        })
    });
});

function showpage(pagenum) {
    $("#table_content").empty();
    currentPage = pagenum;
    for (var i = 0; i < tabledata.length; i++) {
        if (tabledata.length <= pagecount) {
            var trs = "<tr><td>" + tabledata[i].job + "</td><td>" + tabledata[i].user + "</td><td>" + tabledata[i]._class + "</td><td>" + tabledata[i].level
                + "</td><td>" + tabledata[i].item + "</td><td>" + tabledata[i].result + "</td><td>" + tabledata[i].rundate + "</td><td>" + tabledata[i].usetime + "</td><td>" + tabledata[i].mark +"</td></tr>"
            $("#table_content").append(trs)
        } else {
            if ((pagenum - 1) * pagecount <= i && i < pagenum * pagecount) {
                var trs = "<tr><td>" + tabledata[i].job + "</td><td>" + tabledata[i].user + "</td><td>" + tabledata[i]._class + "</td><td>" + tabledata[i].level
                    + "</td><td>" + tabledata[i].item + "</td><td>" + tabledata[i].result + "</td><td>" + tabledata[i].rundate + "</td><td>" + tabledata[i].usetime + "</td><td>" + tabledata[i].mark +"</td></tr>"
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
        url: '/script/getHistoryByJob',
        data: {
            "jobname": search_input
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



// 导出为excel(所查询的结果）
function exportExcel(){
    console.log(tabledata);
    tabledata = [{"id":1,"date":"2021-05-19 11:18:22","job":"rs21-1240as-zltest","user":"zl","_class":"[单只检查]","level":"[外必检]","item":" 检查VIA孔距原稿线路PAD间距是否小于0.25mm","key":"Via_To_Signal_Check","result":"NG","rundate":"2021-05-19 11:21:25","usetime":"2 秒","enable":"","mark":"检测到间距不足:\nnet_zl cs,要求:不小于0.25mm \nnet_zl ss,要求:不小于0.25mm "},{"id":7507,"date":"2021-12-02 18:04:51","job":"rs21-1240as-zlsys","user":"zlsys","_class":"[单只检查]","level":"[外必检]","item":" 检查单层线路网络","key":"SignalNetCheck","result":"OK","rundate":"2021-12-02 18:10:47","usetime":"5 秒","enable":"","mark":"恭喜，该项检查通过."}];

    console.log(JSON.stringify(tabledata));
    // testdata = {"id":1,"date":"2021-05-19 11:18:22","job":"rs21-1240as-zltest","user":"zl","_class":"[单只检查]","level":"[外必检]","item":" 检查VIA孔距原稿线路PAD间距是否小于0.25mm","key":"Via_To_Signal_Check","result":"NG","rundate":"2021-05-19 11:21:25","usetime":"2 秒","enable":"","mark":"检测到间距不足:\nnet_zl cs,要求:不小于0.25mm \nnet_zl ss,要求:不小于0.25mm "},{"id":7507,"date":"2021-12-02 18:04:51","job":"rs21-1240as-zlsys","user":"zlsys","_class":"[单只检查]","level":"[外必检]","item":" 检查单层线路网络","key":"SignalNetCheck","result":"OK","rundate":"2021-12-02 18:10:47","usetime":"5 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34236,"date":"2022-04-06 10:38:14","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 10:44:43","usetime":"0 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34241,"date":"2022-04-06 16:16:27","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 16:22:56","usetime":"1 秒","enable":"","mark":"检测到白油块区域有异物:\nStep:set Layer:css "},{"id":34243,"date":"2022-04-06 16:17:43","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 16:24:11","usetime":"1 秒","enable":"","mark":"检测到白油块区域有异物:\nStep:set Layer:css "},{"id":34245,"date":"2022-04-06 16:18:47","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 16:25:16","usetime":"1 秒","enable":"","mark":"检测到白油块区域有异物:\nStep:set Layer:css "},{"id":34246,"date":"2022-04-06 16:19:47","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 16:26:16","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34247,"date":"2022-04-06 16:24:08","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 16:30:37","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34248,"date":"2022-04-06 16:25:16","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 16:31:45","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34250,"date":"2022-04-06 16:44:38","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 16:51:07","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34251,"date":"2022-04-06 16:45:34","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 16:52:02","usetime":"2 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34252,"date":"2022-04-06 16:47:19","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 16:53:47","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34253,"date":"2022-04-06 16:48:34","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"","rundate":"2022-04-06 16:55:02","usetime":"1 秒","enable":"","mark":"遇到错误,没有返回结果"},{"id":34254,"date":"2022-04-06 17:03:09","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 17:09:38","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34255,"date":"2022-04-06 17:04:01","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"OK","rundate":"2022-04-06 17:10:30","usetime":"1 秒","enable":"","mark":"恭喜，该项检查通过."},{"id":34256,"date":"2022-04-06 17:05:33","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:12:01","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到负性物件:\n:\nStep:set Layer:css \n"},{"id":34257,"date":"2022-04-06 17:06:29","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:12:58","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到负性物件:\nStep:set Layer:css \n"},{"id":34258,"date":"2022-04-06 17:09:14","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:15:43","usetime":"1 秒","enable":"","mark":"检测到白油块区域有异物:\nStep:set Layer:css 当前线路层白油块区域检测到负性物件:\nStep:set Layer:css \n"},{"id":34259,"date":"2022-04-06 17:10:46","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:17:15","usetime":"1 秒","enable":"","mark":"检测到白油块区域有异物:\nStep:set Layer:css \n当前线路层白油块区域检测到负性物件:\nStep:set Layer:css \n"},{"id":34260,"date":"2022-04-06 17:11:58","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:18:27","usetime":"1 秒","enable":"","mark":"检测到白油块区域有异物(正性铜皮):\nStep:set Layer:css \n当前线路层白油块区域检测到负性物件:\nStep:set Layer:css \n"},{"id":34261,"date":"2022-04-06 17:13:16","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:19:45","usetime":"1 秒","enable":"","mark":"当前层检测到多个白油块:\nStep:set Layer:css \n"},{"id":34262,"date":"2022-04-06 17:13:31","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:19:59","usetime":"1 秒","enable":"","mark":"检测到线路层白油块区域有异物(正性铜皮):\nStep:set Layer:css \n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css \n"},{"id":34263,"date":"2022-04-06 17:33:59","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:40:27","usetime":"1 秒","enable":"","mark":"检测到线路层白油块区域有异物(正性物件):\nStep:set Layer:css \n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css \n"},{"id":34264,"date":"2022-04-06 17:34:44","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:41:13","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css \n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css \n"},{"id":34265,"date":"2022-04-06 17:39:41","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:46:09","usetime":"2 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:1\n"},{"id":34266,"date":"2022-04-06 17:40:35","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:47:03","usetime":"2 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:2\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:2\n"},{"id":34267,"date":"2022-04-06 17:41:12","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:47:41","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:2\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:2\n"},{"id":34268,"date":"2022-04-06 17:42:04","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 17:48:33","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:2\n"},{"id":34337,"date":"2022-04-06 19:15:33","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 19:22:02","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:2\n"},{"id":34338,"date":"2022-04-06 19:20:10","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 19:26:38","usetime":"2 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:2\n"},{"id":34339,"date":"2022-04-06 19:20:52","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 19:27:20","usetime":"2 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n"},{"id":34340,"date":"2022-04-06 19:22:26","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"","rundate":"2022-04-06 19:28:54","usetime":"1 秒","enable":"","mark":"遇到错误,没有返回结果"},{"id":34375,"date":"2022-04-06 20:00:27","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 20:06:56","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:2\n"},{"id":34376,"date":"2022-04-06 20:01:01","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 20:07:29","usetime":"2 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:1\n"},{"id":34377,"date":"2022-04-06 20:01:50","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-06 20:08:19","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:1\n"},{"id":34412,"date":"2022-04-07 08:12:22","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-07 08:18:52","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n当前线路层白油块区域检测到异物(负性物件):\nStep:set Layer:css 数量:1\n"},{"id":34413,"date":"2022-04-07 08:13:17","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-07 08:19:47","usetime":"0 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:1\n"},{"id":34414,"date":"2022-04-07 08:14:00","job":"rs21-1240as-zltest","user":"zlsys","_class":"[set检查]","level":"[外必检]","item":" 检测字符层白油块位置在防焊和线路是否有异物","key":"CheckWhiteOilBlockFeatures","result":"NG","rundate":"2022-04-07 08:20:29","usetime":"1 秒","enable":"","mark":"当前线路层白油块区域检测到异物(正性物件):\nStep:set Layer:css 数量:4\n"};
    alert(tabledata);
    $.ajax({
        url:"/excel/export2",
        method:'post',
        contentType: "application/json; charset=utf-8",
        dataType:'json',
        // headers:{
        //     "Content-Type":"application/json"
        // },
        data: JSON.stringify(tabledata),
        success:function (callback) {
            console.log("ok");
        }
    })
}