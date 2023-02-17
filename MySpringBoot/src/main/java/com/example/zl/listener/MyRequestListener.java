package com.example.zl.listener;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import javax.servlet.ServletRequestEvent;
import javax.servlet.ServletRequestListener;
import javax.servlet.http.HttpServletRequest;

@Component
public class MyRequestListener implements ServletRequestListener {
    private static final Logger logger = LoggerFactory.getLogger(MyRequestListener.class);

    @Override
    public void requestDestroyed(ServletRequestEvent sre) {
        logger.info("request end");
        HttpServletRequest request = (HttpServletRequest) sre.getServletRequest();
        logger.info("Request域中保存的name值为：" + request.getAttribute("name"));
    }

    @Override
    public void requestInitialized(ServletRequestEvent sre) {
        HttpServletRequest servletRequest = (HttpServletRequest) sre.getServletRequest();
        logger.info("session id:" + servletRequest.getRequestedSessionId());
        logger.info("session url:" + servletRequest.getRequestURI());
        servletRequest.setAttribute("name","亮");
    }
}
