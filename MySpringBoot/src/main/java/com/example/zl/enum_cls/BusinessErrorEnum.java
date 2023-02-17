package com.example.zl.enum_cls;

/**
 * 错误枚举
 */
public enum BusinessErrorEnum {

    PARAMETER_EXCEPTION("101","参数异常"),
    SERVICE_TIME_OUT("102","服务调用超时"),
    FILE_SIZE_OUT_OF_RANGE("103","文件大小超出范围"),
    UNEXPECTED_EXCEPTION("500","系统异常，请联系管理员");

    private String code;
    private String msg;

    BusinessErrorEnum(String code, String msg) {
        this.code = code;
        this.msg = msg;
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
