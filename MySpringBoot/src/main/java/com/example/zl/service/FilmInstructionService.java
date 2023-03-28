package com.example.zl.service;

import com.example.zl.dao.FilmInstructionMapper;
import com.example.zl.enum_cls.FilmInstructionPager;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Service;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.ResponseBody;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Service
public class FilmInstructionService {

//    protected int count = getPageCount();

    @Resource
    private FilmInstructionMapper filmInstructionMapper;
//    @Resource
//    private ApplicationContext applicationContext;

//    public Blogger getBloggerById(Integer id) {
//        return filmInstructionMapper.selectBloggerById(id);
//    }

    public ArrayList getAllFilmInstruction() {
        return filmInstructionMapper.selectAllFilmInstruction();
    }

    public ArrayList searchFilmInstruction(String name){
        return filmInstructionMapper.selectFilmInstructionByName(name);
    }

    public int getPageCount() {
        int size = getAllFilmInstruction().size();
        int count;
        if ((size % FilmInstructionPager.PAGESIZE) == 0) {
            count = size / FilmInstructionPager.PAGESIZE;
        } else {
            count = size / FilmInstructionPager.PAGESIZE + 1;
        }
        return count;
    }
    public int searchPageCount(String name){
        int size = searchFilmInstruction(name).size();
        int count;
        if ((size % FilmInstructionPager.PAGESIZE) == 0) {
            count = size / FilmInstructionPager.PAGESIZE;
        } else {
            count = size / FilmInstructionPager.PAGESIZE + 1;
        }
        return count;
    }

    //获取对应的filmInstruction
    public String getFilmInstructionOnPage(Model model, int num) {
        ArrayList list = new ArrayList();
        if (num > getPageCount()) {
            model.addAttribute("dataPages", getPageCount());
            model.addAttribute("currentPage", getPageCount());
            model.addAttribute("datalist", list);
        } else {
            int begin = FilmInstructionPager.PAGESIZE * (num - 1);
            list = filmInstructionMapper.selectPageFilmInstruction(begin, FilmInstructionPager.PAGESIZE);
            model.addAttribute("dataPages", getPageCount());
            model.addAttribute("currentPage", num);
            model.addAttribute("datalist", list);
        }
        return "index";
    }
    //按料号查询
    public HashMap searchFilmOnPage(Model model, String name, int num) {
        HashMap hashMap = new HashMap();
        ArrayList list = new ArrayList();
        if (num > searchPageCount(name)) {
            model.addAttribute("dataPages", searchPageCount(name));
            model.addAttribute("currentPage", searchPageCount(name));
            model.addAttribute("datalist", list);
            hashMap.put("dataPages",searchPageCount(name));
            hashMap.put("currentPage",searchPageCount(name));
            hashMap.put("datalist",null);
        } else {
            int begin = FilmInstructionPager.PAGESIZE * (num - 1);
            list = filmInstructionMapper.selectPageFilmInstructionByName(name,begin, FilmInstructionPager.PAGESIZE);
            model.addAttribute("dataPages", searchPageCount(name));
            model.addAttribute("currentPage", num);
            model.addAttribute("datalist", list);
            hashMap.put("dataPages",searchPageCount(name));
            hashMap.put("currentPage",num);
            hashMap.put("datalist",list);
        }
        return hashMap;
    }
}
