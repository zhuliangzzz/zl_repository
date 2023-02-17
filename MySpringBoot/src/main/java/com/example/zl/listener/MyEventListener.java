package com.example.zl.listener;

import com.example.zl.entity.Blogger;
import org.springframework.context.ApplicationListener;
import org.springframework.stereotype.Component;

/**
 * 自定义监听器  监听MyEvent
 */
@Component
public class MyEventListener implements ApplicationListener<MyEvent>{
    @Override
    public void onApplicationEvent(MyEvent event) {
        Blogger blogger = event.getBlogger();
        System.out.println("监听到事件中的name为：" + blogger.getName());
        System.out.println("监听到事件中的pass为：" + blogger.getPass());
    }
}
