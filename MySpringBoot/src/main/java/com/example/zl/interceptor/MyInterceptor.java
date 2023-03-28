package com.example.zl.interceptor;

import com.example.zl.annotation.Uninterception;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.lang.reflect.Method;

public class MyInterceptor implements HandlerInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(MyInterceptor.class);

//    @Override
//    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
//        if (handler instanceof HandlerMethod) {
//            Method method = ((HandlerMethod) handler).getMethod();
//            String name = method.getName();
//            logger.info("拦截到方法{},该方法在执行前被拦截到...", name);
//
//            //通过方法 获取方法上的注解，根据注解判断该方法是否要被拦截
////            Uninterception annotation = method.getAnnotation(Uninterception.class);
////            if(null != annotation){    //有注解，不拦截 ;没有注解，拦截不执行
////                return true;
////            }else{
////                return false;
////            }
////            String token = request.getParameter("token");
////            if (null == token || "".equals(token)) {
////                logger.info("用户未登录，没有权限===========请重新登录");
////                // 返回false取消当前请求
////                return false;
////            }else{
////                // 返回true 继续执行
////                return true;
////            }
//            return true;
//        } else {
//            return true;
//        }
//
//    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if (handler instanceof HandlerMethod) {
            Method method = ((HandlerMethod) handler).getMethod();
            String name = method.getName();
            logger.info("拦截到方法{},该方法在执行前被拦截到...", name);
//            通过方法 获取方法上的注解，根据注解判断该方法是否要被拦截
//            Uninterception annotation = method.getAnnotation(Uninterception.class);
//            if(null != annotation){    //有注解，不拦截 ;没有注解，拦截不执行
//                return true;
//            }else{
//                return false;
//            }
            return true;
//            String token = request.getParameter("token");
//            if (null == token || "".equals(token)) {
//                logger.info("用户未登录，没有权限===========请重新登录");
//                // 返回false取消当前请求
//                return false;
//            }else{
//                // 返回true 继续执行
//                return true;
//            }
        } else {
            return true;
        }

    }

//    @Override
//    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception{
//        HttpSession session = request.getSession();
//        Object user = session.getAttribute("user");
//        if(user==null){
//            response.sendRedirect("/login.html");
//            return false;
//        }
//        return true;
//    }


    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView) throws Exception {
        logger.info("执行完方法后进入执行（controller方法执行之后），还没有进行视图渲染...");
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        logger.info("整个请求已完成，dispatchservlet也完成了视图渲染，可以做一些清理工作...");
    }
}
