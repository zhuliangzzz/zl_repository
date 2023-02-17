package com.example.zl.controller;

import com.example.zl.entity.Blogger;
import com.example.zl.service.BloggerService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;

/**
 * Blogger request
 */
@Controller
@RequestMapping("/blogger")
public class BloggerController {
    @Resource
    private BloggerService bloggerService;

    /**
     * 获取某id的blogger
     *
     * @param id
     * @return
     */
    @GetMapping("/getblogger")
    public String getBloggerById(@RequestParam(value = "id") Integer id, Model model) {
        model.addAttribute("res", bloggerService.getBloggerById(id));
        return "show";
    }

    /**
     * 获取所有用户
     */
    @GetMapping("/getbloggers")
    public String getAllBlogger(Model model) {
        ArrayList allBlogger = bloggerService.getAllBlogger();
        model.addAttribute("res", allBlogger);
        return "show";
    }

    /**
     * 插入用户
     *
     * @return
     */
    @RequestMapping("/add")
    public String addBlogger(Blogger blogger, Model model) {
        String s = bloggerService.addBlogger(blogger);
        model.addAttribute("res", s);
        return "show";
    }

    /**
     * 登录
     *
     * @param blogger
     * @return
     */
    @PostMapping("/login")
    public String login(Blogger blogger, Model model) {
        return bloggerService.login(blogger, model);
    }
}
