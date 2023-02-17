package com.example.zl.dao;

import com.example.zl.entity.Blogger;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

public interface BloggerMapper {
    public Blogger selectBloggerById(Integer id);
    public Blogger selectBloggerByName(String name);
    public ArrayList selectAllBlogger();
    public int insertBlogger(Blogger blogger);
    public ArrayList selectBlogger(Blogger blogger);
    //
    @Insert("insert into blogger(name,password) values (#{name},#{pass})")
    public Integer insertBloggerTest(Blogger blogger);
}
