package com.example.demo;

import com.example.demo.User;
import com.example.demo.DatabaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.CrossOrigin;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:8081")  // 允许来自8080端口的请求
//@CrossOrigin(origins = "http://124.70.51.109:8080")  // 允许来自8080端口的请求
public class UserController {

    @Autowired
    private DatabaseService databaseService;

    @PostMapping("/check-username")
    public Map<String, Boolean> checkUsername(@RequestBody User user) {
        Map<String, Boolean> response = new HashMap<>();
        response.put("exists", databaseService.isUsernameExists(user.getUsername()));
        return response;
    }

    @PostMapping("/register")
    public Map<String, String> registerUser(@RequestBody User user) {
        Map<String, String> response = new HashMap<>();

        // 检查用户名是否已经存在
        if (databaseService.isUsernameExists(user.getUsername())) {
            response.put("status", "error");
            response.put("message", "用户名已存在，请重新输入");
            return response;
        }

        // 用户名不存在，将用户信息保存到数据库
        boolean isSaved = databaseService.saveUser(user);
        if (isSaved) {
            response.put("status", "success");
            response.put("message", "注册成功");
        } else {
            response.put("status", "error");
            response.put("message", "注册失败，请稍后重试");
        }

        return response;
    }

    @PostMapping("/login")
    public Map<String, String> loginUser(@RequestBody User user) {
        Map<String, String> response = new HashMap<>();

        if (!databaseService.isUsernameExists(user.getUsername())) {
            response.put("status", "error");
            response.put("message", "用户名不存在，请重新输入");
            return response;
        }

        if (!databaseService.isPasswordCorrect(user.getUsername(), user.getPassword())) {
            response.put("status", "error");
            response.put("message", "用户名或密码不正确");
            return response;
        }

        response.put("status", "success");
        return response;
    }
}
