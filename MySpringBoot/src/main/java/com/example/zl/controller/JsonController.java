package com.example.zl.controller;

import com.example.zl.entity.User;
import com.example.zl.util.JsonResult;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/json")
public class JsonController {
    @RequestMapping("/user")
    public JsonResult<User> getUser() {
        User user = new User(1, "吕布", "lvbu");
        return new JsonResult<>(user);
    }

    @RequestMapping("/list")
    public JsonResult<List> getUserList() {
        ArrayList<User> users = new ArrayList<>();
        User user = new User(2, "关羽", "guanyu");
        User user2 = new User(3, "张飞", "zhangfei");
        users.add(user);
        users.add(user2);
        return new JsonResult<>(users,"获取用户列表成功");
    }

    @RequestMapping("/map")
    public JsonResult<Map> getUserMap() {
        HashMap<String, Object> map = new HashMap<>();
        map.put("吕布", new User(1, null, null));
        map.put("关羽", new User(2, "关羽", "guanyu"));
        map.put("张飞", new User(3, "张飞", "zhangfei"));
        map.put("test", null);
        return new JsonResult<>(map);
    }
}
