package com.example.zl.controller;

import com.example.zl.entity.Blogger;
import com.example.zl.service.BloggerService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpSession;
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

    //    public String getPageCount(){
//        return bloggerService.getPageCount();
//    }
    @GetMapping("/getBloggerOnPage")
    public String getBloggerOnPage(Model model, @RequestParam(value = "page") int i) {
        return bloggerService.getBloggerOnPage(model, i);
    }

    /**
     * 插入用户
     *
     * @return
     */
    @ResponseBody
    @PostMapping("/add")
    public int addBlogger(Blogger blogger, Model model) {
        return bloggerService.addBlogger(blogger, model);
    }

    /**
     * 删除用户
     *
     * @param id
     * @param model
     * @return
     */
    @PostMapping("/del")
    public String removeBloggerById(int id, Model model) {
        return bloggerService.deleteBloggerById(id, model);
    }

    /**
     * 编辑用户
     *
     * @param blogger
     * @param model
     * @return
     */
    @PostMapping("/edit")
    public String editBlogger(Blogger blogger, Model model) {
        return bloggerService.editBlogger(blogger, model);
    }

    /**
     * 登录
     *
     * @param blogger
     * @return
     */
    @PostMapping("/login")
    public String login(Blogger blogger, Model model, HttpSession session) {
        return bloggerService.login(blogger, model, session);
    }

    @GetMapping("/logout")
    public String logout(Model model, HttpSession session) {
        return bloggerService.logout(model, session);
    }
}
