package com.example.zl.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * aop测试
 */
@RestController
@RequestMapping("/aop")
public class AopController {
    @GetMapping("/test/{name}")
    public String testAop(@PathVariable String name){
        return "name：" + name;
    }
}
