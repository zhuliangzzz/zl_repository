package com.example.zl.handler;

import com.example.zl.exception.BusinessException;
import com.example.zl.util.ExceptionJsonResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * 全局异常处理
 */
@ControllerAdvice
@ResponseBody
public class GlobalExceptionHandler {
    private Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * 参数缺失异常
     *
     * @param ex
     * @return
     */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    @ResponseStatus(value = HttpStatus.BAD_REQUEST)
    public ExceptionJsonResult handleHttpMessageNotReadableException(MissingServletRequestParameterException ex) {
        logger.error("缺少请求参数，{}", ex.getMessage());
        return new ExceptionJsonResult("400", "缺少必要的参数");
    }

    /**
     * 空指针异常
     *
     * @param ex
     * @return
     */
    @ExceptionHandler(NullPointerException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ExceptionJsonResult handleNullPointerException(NullPointerException ex) {
        logger.error("空指针异常，{}", ex.getMessage());
        return new ExceptionJsonResult("500", "空指针异常了");
    }

    /**
     * 处理业务自定义异常
     * @param ex
     * @return
     */
    @ExceptionHandler(BusinessException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ExceptionJsonResult handleBusinessException(BusinessException ex){
        return new ExceptionJsonResult(ex.getCode(),ex.getMsg());
    }
    /**
     * 系统未知异常
     * @param ex
     * @return
     */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ExceptionJsonResult handUnexpectedException(Exception ex) {
        logger.error("系统异常，{}", ex.getMessage());
        return new ExceptionJsonResult("500","系统未知异常，请联系管理员");
    }

}
