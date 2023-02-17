package com.example.zl.util;

public class ExceptionJsonResult {
    protected String code;
    protected String msg;

    public ExceptionJsonResult() {
        this.code= "200";
        this.msg = "操作成功";
    }

    public ExceptionJsonResult(String code, String msg) {
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
