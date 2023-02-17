package com.example.zl.controller;


import com.example.zl.entity.User;
import com.example.zl.enum_cls.BusinessErrorEnum;
import com.example.zl.exception.BusinessException;
import com.example.zl.util.JsonResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/exception")
public class ExceptionController {
    private Logger logger = LoggerFactory.getLogger(ExceptionController.class);

    @RequestMapping("/test")
    public JsonResult exTest(@RequestParam String name,
                                   @RequestParam String pass) {
        logger.info("name:", name);
        logger.info("pass:", pass);
        return new JsonResult();
    }
    @RequestMapping("/business")
    public JsonResult business_exTest() {
        try {
            int i = 1 / 0;
        } catch (Exception e) {
            throw new BusinessException(BusinessErrorEnum.FILE_SIZE_OUT_OF_RANGE);
        }
        return new JsonResult();
    }
}
