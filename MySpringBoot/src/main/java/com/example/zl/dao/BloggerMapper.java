package com.example.zl.dao;

import com.example.zl.entity.Blogger;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

public interface BloggerMapper {
    public Blogger selectBloggerById(Integer id);
    public Blogger selectBloggerByName(String name);
    public ArrayList<Blogger> selectAllBlogger();
    public int insertBlogger(Blogger blogger);
    public ArrayList selectBlogger(Blogger blogger);
    public int deleteBloggerById(Integer id);
    public int updateBlogger(Blogger blogger);
    //获取某页信息
    public ArrayList selectPageBlooger(@Param(value = "begin") int begin, @Param(value = "size")int size);
//    @Insert("insert into blogger(name,password) values (#{name},#{pass})")
    public int insertBloggerTest(Blogger blogger);
}
