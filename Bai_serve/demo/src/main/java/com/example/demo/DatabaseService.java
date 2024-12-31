package com.example.demo;

import org.springframework.stereotype.Service;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

@Service  // 添加 @Service 注解，表示这是一个 Spring 管理的服务类
public class DatabaseService {

    private static final String JDBC_URL = "jdbc:mysql://mysql_baihe:3306/baihe_wbq";
    private static final String JDBC_USER = "root";
    private static final String JDBC_PASSWORD = "woainiaiwo121";

    public Connection connect() {
        Connection connection = null;
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
            connection = DriverManager.getConnection(JDBC_URL, JDBC_USER, JDBC_PASSWORD);
            System.out.println("数据库连接成功！");
        } catch (SQLException | ClassNotFoundException e) {
            System.err.println("数据库连接失败: " + e.getMessage());
        }
        return connection;
    }
    // 检查用户名是否存在
    public boolean isUsernameExists(String username) {
        String query = "SELECT COUNT(*) FROM users WHERE username = ?";
        try (Connection conn = connect();
             PreparedStatement stmt = conn.prepareStatement(query)) {
            stmt.setString(1, username);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getInt(1) > 0;
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return false;
    }

    // 保存用户信息到数据库
    public boolean saveUser(User user) {
        String insert = "INSERT INTO users (username, password) VALUES (?, ?)";
        try (Connection conn = connect();
             PreparedStatement stmt = conn.prepareStatement(insert)) {
            stmt.setString(1, user.getUsername());
            stmt.setString(2, user.getPassword());
            stmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    // 检查密码是否正确
    public boolean isPasswordCorrect(String username, String password) {
        String query = "SELECT password FROM users WHERE username = ?";
        try (Connection conn = connect();
             PreparedStatement stmt = conn.prepareStatement(query)) {
            stmt.setString(1, username);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getString("password").equals(password);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return false;
    }

}
