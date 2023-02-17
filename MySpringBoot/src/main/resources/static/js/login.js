$(function () {
    $("#loginForm").ajaxForm({
        resetForm: true,
        clearForm: true,
        //定义返回JSON数据，还包括xml和script格式
        dataType: 'json',
//      在发送之前进行的操作，如果有问题，返回false即可不会进行提交
        success: function (data) {
            $("#loginForm") .resetForm();
            // alert(JSON.stringify(data));
            //提交成功后调用
            console.log(data);
            // window.location.href="html/index.html";
        },
        error:function(){
            //清空输入框，加上提示框
            $("#js-flash-container .flash").text("Incorrect username or password.");
        }
    });
})

