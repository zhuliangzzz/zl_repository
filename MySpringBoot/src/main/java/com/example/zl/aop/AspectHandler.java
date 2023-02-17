package com.example.zl.aop;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.Signature;
import org.aspectj.lang.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;

/**
 * aop
 * 切面处理类
 */
@Aspect
@Component
public class AspectHandler {
    private final Logger logger = LoggerFactory.getLogger(this.getClass());

    /**
     * 定义一个切面，拦截com.example.zl.controller包和子包下的所有方法
     */
    @Pointcut("execution(* com.example.zl.controller..*.*(..))")
    public void pointCut() {
    }

    @Before("pointCut()")
    public void doBefore(JoinPoint joinPoint) {
        logger.info("==========doBefore方法执行==========");
        Signature signature = joinPoint.getSignature();
        String declaringTypeName = signature.getDeclaringTypeName();
        String name = signature.getName();
        logger.info("即将执行的方法为：{}，属于{}包", name, declaringTypeName);
        ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        HttpServletRequest request = attributes.getRequest();
        //requestUrl
        String requestURL = request.getRequestURL().toString();
        String remoteAddr = request.getRemoteAddr();
        logger.info("请求的url为：{}，ip为：{}", requestURL, remoteAddr);
    }

    @After("pointCut()")
    public void doAfter(JoinPoint joinPoint) {
        logger.info("==========doAfter方法执行==========");
        Signature signature = joinPoint.getSignature();
        String method = signature.getName();
        logger.info("方法{}执行完...", method);
    }

    @AfterReturning(value = "pointCut()", returning = "result")
    public void doAfterReturn(JoinPoint joinPoint, Object result) {
        Signature signature = joinPoint.getSignature();
        String name = signature.getName();
        logger.info("方法{}执行结束，返回参数为：{}", name, result);
        //返回值增强
        logger.info("对返回参数增强：{}", result + "增强");
    }

    @AfterThrowing(value = "pointCut()", throwing = "ex")
    public void doAfterThrow(JoinPoint joinPoint, Throwable ex) {
        Signature signature = joinPoint.getSignature();
        String name = signature.getName();
        logger.info("执行方法{}出错，产生异常：{}", name, ex);
    }

}
