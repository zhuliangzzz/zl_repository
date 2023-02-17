package com.example.zl.controller;

import com.example.zl.entity.Blogger;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import java.lang.reflect.Array;
import java.util.ArrayList;

@Controller
@RequestMapping("/thymeleaf")
public class ThymeleafController {
    @RequestMapping("/test404")
    public String test404() {
        return "404";
    }

    @RequestMapping("/test500")
    public String test500() {
        int i = 5 / 0;
        return "index";
    }

    @GetMapping("/getBlogger")
    public String getBlogger(Model model) {
        Blogger blog = new Blogger(1L, "小明", "123456");
        model.addAttribute("blogger", blog);
        return "blogger";
    }

    @GetMapping("/getBloggerList")
    public String getBloggerList(Model model) {
        ArrayList<Blogger> list = new ArrayList<>();
        Blogger blog = new Blogger(1L, "小明", "123456");
        Blogger blog2 = new Blogger(2L, "小刘", "654321");
        list.add(blog);
        list.add(blog2);
        model.addAttribute("blogList", list);
        return "blogger-list";
    }
}
