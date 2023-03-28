package com.example.zl.controller;


import com.example.zl.service.FilmInstructionService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;

@Controller
@RequestMapping("/film")
public class FilmInstructionController {
    @Resource
    private FilmInstructionService filmInstructionService;

    @GetMapping("/getFilmOnPage")
    public String getFilmOnPage(Model model, @RequestParam(value = "page") int i) {
        return filmInstructionService.getFilmInstructionOnPage(model, i);
    }

    @GetMapping("/selectFilmByName")
    public ArrayList selectFilmByName(@RequestParam(value = "name") String name) {
        return filmInstructionService.searchFilmInstruction(name);
    }
    @ResponseBody
    @PostMapping("/searchFilmOnPage")
    public HashMap searchFilmOnPage(Model model, @RequestParam(value = "name")String name, @RequestParam(value = "page") int i) {
        return filmInstructionService.searchFilmOnPage(model, name,i);
    }
}
