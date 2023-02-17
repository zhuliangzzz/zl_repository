package com.example.zl.exception;

import com.example.zl.enum_cls.BusinessErrorEnum;

/**
 * 异常类
 */
public class BusinessException extends RuntimeException{

    private static final long serialVersionUID = 9115748293486096256L;
    private String code;
    private String msg;

    public BusinessException(BusinessErrorEnum businessEnum) {
        this.code = businessEnum.getCode();
        this.msg = businessEnum.getMsg();
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }
}
