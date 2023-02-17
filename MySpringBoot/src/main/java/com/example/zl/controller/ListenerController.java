package com.example.zl.controller;

import com.example.zl.entity.Blogger;
import com.example.zl.service.BloggerService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.servlet.ServletContext;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

@RestController
@RequestMapping("/listener")
public class ListenerController {
    @Resource
    private BloggerService bloggerService;

    @GetMapping("/getBlogger")
    public Blogger getBlogger(HttpServletRequest request) {
        ServletContext servletContext = request.getServletContext();
        return (Blogger) servletContext.getAttribute("blog");
    }

    @GetMapping("/count")  //session销毁方法未执行
    public String showCountOnLine(HttpServletRequest request) {
        Integer count = (Integer) request.getSession().getServletContext().getAttribute("count");
        return "当前在线人数为：" + count;
    }

    //解决session关闭不执行销毁的问题
    //把原来的 sessionId 记录在浏览器中，下次再打开时，把这个 sessionId 传过去，这样服务器就不会重新再创建了
//    @GetMapping("/count2")
//    public String showCountOnLine2(HttpServletRequest request, HttpServletResponse response) {
//        Cookie cookie;
//        try {
//            //把sessionId记录在浏览器中   //jsessionid
//            cookie = new Cookie("JSESSIONID", URLEncoder.encode(request.getSession().getId(), "utf8"));
//            cookie.setPath("/");
//            cookie.setMaxAge(48 * 60 * 60);
//            response.addCookie(cookie);
//        } catch (UnsupportedEncodingException e) {
//            e.printStackTrace();
//        }
//        Integer count = (Integer) request.getSession().getServletContext().getAttribute("count");
//        return "当前在线人数为：" + count;
//    }

    //测试myRequestListener
    @GetMapping("/request")
    public String testRequestListener(HttpServletRequest request) {
        System.out.println("request中的name值：" + request.getAttribute("name"));
        return "success";
    }

    @GetMapping("/publish")
    public String publish() {
        Blogger blogger = bloggerService.publishMyEvent();
        System.out.println(blogger);
        return "success";
    }

}
