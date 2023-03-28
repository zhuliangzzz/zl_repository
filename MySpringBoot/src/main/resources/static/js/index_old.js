

$(function(){

//   //获取用户信息
    $("#flushBtn").on("click",getData);
})

function getData(){
    var tbody = $("#customerInfo");
    tbody.empty();
    $.ajax({
        url:"/Cus/getCustomers",
        method:"get",
        success:function(data){
            var text = '';
            for(var i=0;i<data.length;i++){
                // console.log(data[i])
                var obj = data[i];
                text += "<tr><td>"+obj['id']+"</td><td>"+ obj['username'] + "</td><td>"
                    + obj['password'] + "</td><td>"+ obj['sex'] + "</td><td>"
                    + obj['address'] + "</td></tr>";
            }
            tbody.append(text);
        }
    })
}