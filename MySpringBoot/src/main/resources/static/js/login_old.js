$(function(){
    $("form div input").on("focus",function(){
        $(this).removeClass("inputouter");
        $(this).addClass("inputouter_focus");
        $(this).siblings("label").addClass("input_tips_focus");
    });
    $("form div input").on("blur",function(){
        $(this).removeClass("inputouter_focus");
        $(this).addClass("inputouter");
        $(this).siblings("label").removeClass("input_tips_focus");
    });
    $("form div input").on("input",function(){
        if($(this).val() != ""){
            $(this).siblings("label").css("display","none");
        }else{
            $(this).siblings("label").css("display","block");
        }
    })
});

