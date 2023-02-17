package com.example.zl.service;

import com.example.zl.dao.BloggerMapper;
import com.example.zl.entity.Blogger;
import com.example.zl.listener.MyEvent;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.ArrayList;

@Service
public class BloggerService {
    @Resource
    private BloggerMapper bloggerMapper;
    @Resource
    private ApplicationContext applicationContext;

    public Blogger getBloggerById(Integer id) {
        return bloggerMapper.selectBloggerById(id);
    }

    public ArrayList getAllBlogger() {
        return bloggerMapper.selectAllBlogger();
    }

    public String addBlogger(Blogger blogger) {
        Blogger thisBlogger = bloggerMapper.selectBloggerByName(blogger.getName());
        if (thisBlogger == null) {
            int i = bloggerMapper.insertBlogger(blogger);
            if (i > 0) {
                return "添加成功";
            } else {
                return "添加失败";
            }
        } else {
            return "该用户已存在";
        }

    }

    public String login(Blogger blogger) {
        ArrayList res = bloggerMapper.selectBlogger(blogger);
        if (res.size() > 0) {
            if ("admin".equals(blogger.getName())) {
                return "admin/index";
            } else {
                return "index";
            }
        } else {
            return "redict:login";
        }
    }

    //事务测试
    @Transactional(rollbackFor = Exception.class)
    public void insertBloggerTest(Blogger b) {
        bloggerMapper.insertBloggerTest(b);
    }

    //发布监听事件myevent
    public Blogger publishMyEvent() {
        Blogger blogger = new Blogger(1L, "admin", "123654");
        applicationContext.publishEvent(new MyEvent(this, blogger));
        return blogger;
    }
}
