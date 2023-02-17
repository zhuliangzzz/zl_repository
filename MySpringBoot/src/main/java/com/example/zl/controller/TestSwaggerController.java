package com.example.zl.controller;

import com.example.zl.entity.User;
import com.example.zl.util.JsonResult;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("swagger")
@Api(value = "TestSwaggerController接口Api")
public class TestSwaggerController {
    @GetMapping("/get/{id}")
    @ApiOperation("根据用户唯一标识获取用户信息")
    public JsonResult<User> getUserInfo(@PathVariable @ApiParam(value = "用户唯一标识") Integer id) {
        User user = new User(id, "name", "name");
        return new JsonResult<>(user);
    }
}
