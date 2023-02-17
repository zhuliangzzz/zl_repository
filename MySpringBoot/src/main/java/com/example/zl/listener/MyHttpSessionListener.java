package com.example.zl.listener;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import javax.servlet.http.HttpSessionEvent;
import javax.servlet.http.HttpSessionListener;

@Component
public class MyHttpSessionListener implements HttpSessionListener {
    private static final Logger logger = LoggerFactory.getLogger(MyHttpSessionListener.class);
    private int count;

    @Override
    public synchronized void sessionCreated(HttpSessionEvent se) {
        logger.info("新用户上线了...");
        count++;
        logger.info("上线人数：" + count);
        se.getSession().getServletContext().setAttribute("count", count);
    }

    @Override
    public synchronized void sessionDestroyed(HttpSessionEvent se) {
        logger.info("该用户下线中...");
        count--;
//        logger.info("在线人数：" + count);
        se.getSession().getServletContext().setAttribute("count", count);
    }
}
