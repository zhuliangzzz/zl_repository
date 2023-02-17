package com.example.zl.controller;

import com.example.zl.annotation.Uninterception;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/interceptor")
public class InterceptorController {
    @GetMapping("/test")
    public String testInterceptor(){
        return "index";
    }
}
