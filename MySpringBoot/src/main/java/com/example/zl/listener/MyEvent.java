package com.example.zl.listener;

import com.example.zl.entity.Blogger;
import org.springframework.context.ApplicationEvent;


/**
 * 自定义监听事件
 */
public class MyEvent extends ApplicationEvent {

    private static final long serialVersionUID = -849990933420233818L;
    public Blogger blogger;

    public MyEvent(Object source, Blogger blogger) {
        super(source);
        this.blogger = blogger;
    }

    public Blogger getBlogger() {
        return blogger;
    }

    public void setBlogger(Blogger blogger) {
        this.blogger = blogger;
    }
}
