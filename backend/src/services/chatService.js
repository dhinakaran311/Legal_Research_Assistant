/**
 * Chat Service
 * Manages ChatSession + ChatMessage persistence and AI Engine communication.
 */
import { PrismaClient } from '@prisma/client';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();
const AI_ENGINE_URL = process.env.AI_ENGINE_URL || 'http://localhost:5000';
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

// ── Session management ────────────────────────────────────────────────────────

export async function createSession(userId = null) {
  return prisma.chatSession.create({
    data: { userId },
    include: { messages: true },
  });
}

export async function getSession(sessionId) {
  return prisma.chatSession.findUnique({
    where: { id: sessionId },
    include: {
      messages: { orderBy: { createdAt: 'asc' } },
    },
  });
}

export async function getSessions(userId = null) {
  const where = userId ? { userId } : {};
  return prisma.chatSession.findMany({
    where,
    orderBy: { updatedAt: 'desc' },
    include: {
      messages: {
        orderBy: { createdAt: 'desc' },
        take: 1, // last message for preview
      },
    },
  });
}

export async function clearSession(sessionId) {
  await prisma.chatSession.delete({ where: { id: sessionId } });
  return true;
}

// ── Message management ────────────────────────────────────────────────────────

export async function saveMessage(sessionId, role, content, metadata = null) {
  const message = await prisma.chatMessage.create({
    data: { sessionId, role, content, metadata },
  });

  // Update session title from first user message
  if (role === 'user') {
    const session = await prisma.chatSession.findUnique({ where: { id: sessionId } });
    if (session && !session.title) {
      await prisma.chatSession.update({
        where: { id: sessionId },
        data: {
          title: content.slice(0, 60) + (content.length > 60 ? '...' : ''),
          updatedAt: new Date(),
        },
      });
    } else {
      await prisma.chatSession.update({
        where: { id: sessionId },
        data: { updatedAt: new Date() },
      });
    }
  }

  return message;
}

export async function getHistory(sessionId) {
  return prisma.chatMessage.findMany({
    where: { sessionId },
    orderBy: { createdAt: 'asc' },
  });
}

// ── AI Engine communication ───────────────────────────────────────────────────

export async function sendToAIEngine(sessionId, message, useLlm = true, useCrew = false) {
  if (!INTERNAL_API_KEY) {
    throw new Error('INTERNAL_API_KEY not configured');
  }

  const response = await axios.post(
    `${AI_ENGINE_URL}/api/chat`,
    { session_id: sessionId, message, use_llm: useLlm, use_crew: useCrew },
    {
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API-Key': INTERNAL_API_KEY,
      },
      timeout: 120000,
    }
  );

  return response.data;
}

export async function getAIEngineHistory(sessionId) {
  if (!INTERNAL_API_KEY) return { messages: [] };

  try {
    const response = await axios.get(
      `${AI_ENGINE_URL}/api/chat/${sessionId}/history`,
      {
        headers: { 'X-Internal-API-Key': INTERNAL_API_KEY },
        timeout: 10000,
      }
    );
    return response.data;
  } catch {
    return { messages: [] };
  }
}
