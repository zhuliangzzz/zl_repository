package com.example.zl.listener;

import com.example.zl.entity.Blogger;
import com.example.zl.service.BloggerService;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationListener;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.stereotype.Component;

import javax.servlet.ServletContext;

/**
 * 应用内存储一个blog对象
 */
@Component
public class MyContextListener implements ApplicationListener<ContextRefreshedEvent> {
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        ApplicationContext applicationContext = event.getApplicationContext();
        BloggerService bloggerService = applicationContext.getBean(BloggerService.class);
        Blogger blog = bloggerService.getBloggerById(1);
        ServletContext context = applicationContext.getBean(ServletContext.class);
        context.setAttribute("blog", blog);
    }
}
