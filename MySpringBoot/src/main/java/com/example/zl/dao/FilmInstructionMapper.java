package com.example.zl.dao;

import com.example.zl.entity.Blogger;
import com.example.zl.entity.FilmInstruction;
import org.apache.ibatis.annotations.Param;

import java.util.ArrayList;

public interface FilmInstructionMapper {
    public FilmInstruction selectFilmInstructionById(Integer id);
    public ArrayList<FilmInstruction> selectFilmInstructionByName(@Param(value = "name")String name);
    public ArrayList<FilmInstruction> selectAllFilmInstruction();
    public ArrayList<FilmInstruction> selectPageFilmInstructionByName(@Param(value = "name")String name, @Param(value = "begin")int begin, @Param(value = "size")int size);
//    public int insertFilmInstruction(FilmInstruction filmInstruction);
//    public ArrayList selectFilmInstruction(FilmInstruction filmInstruction);
//    public int deleteFilmInstructionById(Integer id);
//    public int updateBlogger(FilmInstruction filmInstruction);
    //获取某页信息
    public ArrayList selectPageFilmInstruction(@Param(value = "begin") int begin, @Param(value = "size") int size);
//    @Insert("insert into blogger(name,password) values (#{name},#{pass})")
//    public int insertBloggerTest(Blogger blogger);
}
