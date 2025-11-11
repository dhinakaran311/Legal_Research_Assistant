import express from "express";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();
const router = express.Router();

router.post("/", async (req, res) => {
  const { userId, documentId, comment, helpful } = req.body;
  const feedback = await prisma.feedback.create({
    data: { userId, documentId, comment, helpful },
  });
  res.json(feedback);
});

router.get("/", async (req, res) => {
  const feedbacks = await prisma.feedback.findMany({
    orderBy: { createdAt: "desc" },
  });
  res.json(feedbacks);
});

export default router;
