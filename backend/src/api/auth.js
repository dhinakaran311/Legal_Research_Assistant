import express from "express";
import bcrypt from "bcryptjs";
import { PrismaClient } from "@prisma/client";
import { generateToken } from "../utils/generateToken.js";

const prisma = new PrismaClient();
const router = express.Router();

// Signup
router.post("/signup", async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ message: "Please provide all fields" });
    }

    const userExists = await prisma.user.findUnique({ where: { email } });
    if (userExists) {
      return res.status(400).json({ message: "User already exists" });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const newUser = await prisma.user.create({
      data: { 
        name, 
        email, 
        password: hashedPassword,
        role: "USER" // Add default role
      },
    });

    // Remove password from response
    const { password: _, ...userWithoutPassword } = newUser;
    
    const token = generateToken(newUser.id);
    res.status(201).json({ user: userWithoutPassword, token });
  } catch (error) {
    console.error("Signup error:", error);
    res.status(500).json({ message: "Server error during signup" });
  }
});

// Login
router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: "Please provide email and password" });
    }

    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) {
      return res.status(400).json({ message: "Invalid credentials" });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ message: "Invalid credentials" });
    }

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;
    
    const token = generateToken(user.id);
    res.json({ user: userWithoutPassword, token });
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ message: "Server error during login" });
  }
});

// Google Login
router.post("/google", async (req, res) => {
  try {
    const { name, email, profile_picture } = req.body;

    if (!email) {
      return res.status(400).json({ message: "Email is required" });
    }

    // Check if user already exists
    let user = await prisma.user.findUnique({ where: { email } });

    if (user) {
      // Update profile picture if it changed
      if (profile_picture && user.profile_picture !== profile_picture) {
        user = await prisma.user.update({
          where: { email },
          data: { profile_picture },
        });
      }
    } else {
      // Create new user (no password needed for Google auth)
      user = await prisma.user.create({
        data: {
          name: name || email.split("@")[0],
          email,
          profile_picture: profile_picture || null,
          role: "USER",
        },
      });
    }

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;

    const token = generateToken(user.id);
    res.json({ user: userWithoutPassword, token });
  } catch (error) {
    console.error("Google login error:", error);
    res.status(500).json({ message: "Server error during Google login" });
  }
});

export default router;