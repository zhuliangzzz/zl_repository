package com.example.zl.controller;

import com.example.zl.entity.Blogger;
import com.example.zl.entity.MicroServiceUrl;
import com.example.zl.entity.User;
import com.example.zl.service.BloggerService;
import com.example.zl.util.JsonResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.websocket.server.PathParam;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("test")
public class TestController {
    private final static Logger log = LoggerFactory.getLogger(TestController.class);
    @Resource
    private MicroServiceUrl microServiceUrl;
    @Resource
    private BloggerService bloggerService;

    @RequestMapping("hello")
    public String test() {
        return "hello world";
    }

    @RequestMapping("/log")
    public String testLog() {
        log.error("==========测试error级别的日志打印==========");
        log.warn("==========测试warn级别的日志打印==========");
        log.info("==========测试info级别的日志打印==========");
        log.debug("==========测试debug级别的日志打印==========");
        String str1 = "zhuliang";
        String str2 = "1639329508@qq.com";
        log.info("==========name:{},email:{}==========", str1, str2);
        return "success";
    }

    @RequestMapping("/urls")
    public String getUrls() {
        log.info("==========获取订单服务地址：{}==========", microServiceUrl.getOrderUrl());
        log.info("==========获取用户服务地址：{}==========", microServiceUrl.getUserUrl());
        log.info("==========获取购物服务地址：{}==========", microServiceUrl.getShoppingUrl());
        return "getMicroServiceUrl.......";
    }

    @GetMapping("/test/{idvar}/{name}")
    public String getPathVariable(@PathVariable("idvar") Integer id, @PathVariable String name) {
        log.info("获取到id:" + id);
        log.info("获取到name:" + name);
        return "success";
    }

    @RequestMapping("/test")
    public String getPathParam(@RequestParam String no, @RequestParam(value = "alias", required = false) String attr) {
        log.info("获取到no属性值：" + no);
        log.info("获取到attr属性值：" + attr);
        return "success";
    }

    //    @PathValiable 是从 url 模板中获取参数值
    //    @RequestParam 注解用于 GET 请求上时，接收拼接在 url 中的参数。除此之外，该注解还可以用于 POST 请求，接收前端表单提交的参数
    @PostMapping("/form")
    public String testForm(@RequestParam String username, @RequestParam String password) {
        log.info("username:" + username + ",password:" + password);
        return "get form";
    }

    @PostMapping("/form2")
    public String testForm2(@RequestBody User user) {
        log.info("表单的username:" + user.getUsername());
        log.info("表单的password:" + user.getPassword());
        return "success";
    }

//    @GetMapping("/getblogger")
//    public JsonResult<Blogger> getBloggerById(@RequestParam(value = "id") Integer id) {
//
//        log.info(bloggerService.getBloggerById(id).toString());
//        return new JsonResult<>(bloggerService.getBloggerById(id));
//    }
//
//    @GetMapping("/getbloggers")
//    public void getAllBlogger() {
//        log.info(bloggerService.getAllBlogger().toString());
////        System.out.println(bloggerService.getAllBlogger());
//    }
//    @RequestMapping("/add")
//    public JsonResult addBlogger() {
//        Blogger blogger = new Blogger("liangzhu", "654321");
//        bloggerService.addBlogger(blogger);
//        return new JsonResult();
//    }
    @PostMapping("/addBlogger")
    public synchronized String testInsertBlogger(Blogger blogger) throws SQLException {
        if(null!=blogger){
            bloggerService.insertBloggerTest(blogger);
            return "success";
        }else{
            return "fail";
        }
    }

}
