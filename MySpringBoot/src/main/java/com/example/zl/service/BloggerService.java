package com.example.zl.service;

import com.example.zl.dao.BloggerMapper;
import com.example.zl.entity.Blogger;
import com.example.zl.entity.FilmInstruction;
import com.example.zl.enum_cls.BloggerPager;
import com.example.zl.listener.MyEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ui.Model;

import javax.annotation.Resource;
import javax.servlet.http.HttpSession;
import java.util.ArrayList;

@Service
public class BloggerService {
    @Resource
    private BloggerMapper bloggerMapper;
    @Autowired
    private FilmInstructionService filmInstructionService;
    @Resource
    private ApplicationContext applicationContext;

    public Blogger getBloggerById(Integer id) {
        return bloggerMapper.selectBloggerById(id);
    }

    public ArrayList getAllBlogger() {
        return bloggerMapper.selectAllBlogger();
    }

    public int getPageCount() {
        int count;
        if ((getAllBlogger().size() % BloggerPager.PAGESIZE) == 0) {
            count = getAllBlogger().size() / BloggerPager.PAGESIZE;
        } else {
            count = getAllBlogger().size() / BloggerPager.PAGESIZE + 1;
        }
        return count;
    }

    public String getBloggerOnPage(Model model, int num) {
        ArrayList list = new ArrayList();
        if (num > getPageCount()) {
            model.addAttribute("bloggerPages", getPageCount());
            model.addAttribute("currentPage", getPageCount());
            model.addAttribute("bloggerlist", list);
        } else {
            int begin = BloggerPager.PAGESIZE * (num - 1);
            list = bloggerMapper.selectPageBlooger(begin, BloggerPager.PAGESIZE);
            System.out.println(list);
            model.addAttribute("bloggerPages", getPageCount());
            model.addAttribute("currentPage", num);
            model.addAttribute("bloggerlist", list);
        }
        System.out.println(list);
        return "admin/index";
    }

    //    public int addBlogger(Blogger blogger, Model model) {
//        Blogger thisBlogger = bloggerMapper.selectBloggerByName(blogger.getName());
//        if (thisBlogger == null) {
//            int i = bloggerMapper.insertBlogger(blogger);
//            System.out.println("返回结果：" + i);
//            loadAdminIndex(model);
//            if (i > 0) {
//                System.out.println("用户：" + blogger.getName() + "添加成功");
//                return 1;
//            } else {
//                System.out.println("用户：" + blogger.getName() + "添加失败");
//                return 0;
//            }
//        } else {
//            System.out.println(blogger.getName() + "该用户已存在");
//            return -1;
//        }
//    }
    public int addBlogger(Blogger blogger, Model model) {
        Blogger thisBlogger = bloggerMapper.selectBloggerByName(blogger.getName());
        if (thisBlogger == null) {
            int i = bloggerMapper.insertBlogger(blogger);
            System.out.println("返回结果：" + i);
            getBloggerOnPage(model, 1);
            if (i > 0) {
                System.out.println("用户：" + blogger.getName() + "添加成功");
                return 1;
            } else {
                System.out.println("用户：" + blogger.getName() + "添加失败");
                return 0;
            }
        } else {
            System.out.println(blogger.getName() + "该用户已存在");
            return -1;
        }
    }


    //    public String deleteBloggerById(Integer id, Model model) {
//        int i = bloggerMapper.deleteBloggerById(id);
//        if (i == 1) {
//            System.out.println("用户删除成功，id为" + id);
//        } else {
//            System.out.println("删除失败");
//        }
//        return loadAdminIndex(model);
//    }
    public String deleteBloggerById(Integer id, Model model) {
        int i = bloggerMapper.deleteBloggerById(id);
        if (i == 1) {
            System.out.println("用户删除成功，id为" + id);
        } else {
            System.out.println("删除失败");
        }
        return getBloggerOnPage(model, 1);
    }

    //    //编辑用户updateBlogger
//    public String editBlogger(Blogger blogger, Model model) {
//        int i = bloggerMapper.updateBlogger(blogger);
//        if (i == 1) {
//            System.out.println("用户" + blogger.getName() + "更新成功");
//        } else {
//            System.out.println("用户" + blogger.getName() + "更新失败");
//        }
//        return loadAdminIndex(model);
//    }
    //编辑用户updateBlogger
    public String editBlogger(Blogger blogger, Model model) {
        int i = bloggerMapper.updateBlogger(blogger);
        if (i == 1) {
            System.out.println("用户" + blogger.getName() + "更新成功");
        } else {
            System.out.println("用户" + blogger.getName() + "更新失败");
        }
        return getBloggerOnPage(model, 1);
    }

//    public String loadAdminIndex(Model model) {
//        ArrayList list = getAllBlogger();
//        model.addAttribute("bloggerlist", list);
//        return "admin/index";
//    }

    //    public String login(Blogger blogger, Model model) {
//        ArrayList res = bloggerMapper.selectBlogger(blogger);
//        if (res.size() > 0) {
//            model.addAttribute("user", blogger.getName());
//            if ("admin".equals(blogger.getName())) {
//                return loadAdminIndex(model);
//            } else {
//                return "index";
//            }
//        } else {
//            model.addAttribute("tip", "Incorrect username or password.");
//            return "login";
//        }
//    }
    public String login(Blogger blogger, Model model, HttpSession session) {
        ArrayList res = bloggerMapper.selectBlogger(blogger);
        if (res.size() > 0) {
            session.setAttribute("user", blogger);
//            model.addAttribute("user", blogger.getName());
            if ("admin".equals(blogger.getName())) {
                return getBloggerOnPage(model, 1);
            } else {
                return filmInstructionService.getFilmInstructionOnPage(model, 1);
            }
        } else {
            model.addAttribute("tip", "Incorrect username or password.");
            return "login";
        }
    }

    //注销登录
    public String logout(Model model,HttpSession session) {
//        model.addAttribute("user", null);
        model.addAttribute("bloggerlist", null);
        session.invalidate();
        return "redirect:/template/login.html";
    }

    //事务测试
    @Transactional(rollbackFor = Exception.class)
    public void insertBloggerTest(Blogger b) {
        bloggerMapper.insertBloggerTest(b);
    }

    //发布监听事件myevent
    public Blogger publishMyEvent() {
        Blogger blogger = new Blogger(1L, "admin", "123654");
        applicationContext.publishEvent(new MyEvent(this, blogger));
        return blogger;
    }
}
