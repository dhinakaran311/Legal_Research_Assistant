/**
 * Chat Stream Proxy Route
 * POST /api/chat/stream
 *
 * Security fix: proxies the AI Engine SSE stream through the Node.js backend.
 * - User authenticates with a JWT (never the INTERNAL_API_KEY)
 * - INTERNAL_API_KEY is used server-side only
 * - Messages are persisted to PostgreSQL before and after streaming
 */
import express from 'express';
import axios from 'axios';
import { protect } from '../middleware/authMiddleware.js';
import * as chatService from '../services/chatService.js';

const router = express.Router();

const AI_ENGINE_URL = process.env.AI_ENGINE_URL || 'http://localhost:5000';
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

router.post('/stream', protect, async (req, res) => {
  const { sessionId, message, useLlm = true } = req.body;
  const userId = req.user; // set by authMiddleware.protect

  if (!message || !message.trim()) {
    return res.status(400).json({ error: 'message is required' });
  }

  if (!INTERNAL_API_KEY) {
    return res.status(500).json({ error: 'AI Engine API key not configured on server' });
  }

  // --- Ensure session exists (create if not provided) ---
  let currentSessionId = sessionId;
  if (!currentSessionId) {
    try {
      const session = await chatService.createSession(userId);
      currentSessionId = session.id;
    } catch (err) {
      console.error('Failed to create chat session:', err);
      return res.status(500).json({ error: 'Failed to create session' });
    }
  }

  // --- Save user message to DB ---
  try {
    await chatService.saveMessage(currentSessionId, 'user', message);
  } catch (err) {
    console.error('Failed to save user message:', err);
    // Non-fatal — continue streaming
  }

  // --- Set up SSE headers ---
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  // Send session_id first so client knows which session is active
  res.write(`data: ${JSON.stringify({ type: 'session_id', session_id: currentSessionId })}\n\n`);

  // --- Forward to AI Engine as a streaming request ---
  let fullAnswer = '';
  let doneMetadata = {};

  try {
    const aiResponse = await axios({
      method: 'post',
      url: `${AI_ENGINE_URL}/api/chat/stream`,
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API-Key': INTERNAL_API_KEY,
      },
      data: {
        session_id: currentSessionId,
        message: message.trim(),
        use_llm: useLlm,
      },
      responseType: 'stream',
      timeout: 180000, // 3 min
    });

    const stream = aiResponse.data;
    let buffer = '';

    stream.on('data', (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (!raw) continue;

        try {
          const payload = JSON.parse(raw);

          if (payload.type === 'token') {
            fullAnswer += payload.content || '';
            // Forward token to browser
            res.write(`data: ${JSON.stringify(payload)}\n\n`);

          } else if (payload.type === 'done') {
            // Save assistant response to DB with rich metadata
            doneMetadata = payload;
            const metadata = {
              intent: payload.intent || 'unknown',
              confidence: payload.confidence || 0,
              processing_time_ms: payload.processing_time_ms || 0,
              sources: payload.sources || [],
              graph_references: payload.graph_references || [],
              web_sources: payload.web_sources || [],
              streamed: true,
            };

            chatService
              .saveMessage(currentSessionId, 'assistant', fullAnswer, metadata)
              .catch((err) => console.error('Failed to save assistant message:', err));

            // Forward done event (include session_id from our server)
            res.write(
              `data: ${JSON.stringify({
                ...payload,
                session_id: currentSessionId,
              })}\n\n`
            );

          } else if (payload.type === 'error') {
            res.write(`data: ${JSON.stringify(payload)}\n\n`);

          } else {
            // Pass through any other event types
            res.write(`data: ${JSON.stringify(payload)}\n\n`);
          }
        } catch {
          // Malformed JSON chunk — ignore
        }
      }
    });

    stream.on('end', () => {
      // Flush remaining buffer
      if (buffer.startsWith('data: ')) {
        res.write(`${buffer}\n\n`);
      }
      res.end();
    });

    stream.on('error', (err) => {
      console.error('AI Engine stream error:', err.message);
      res.write(
        `data: ${JSON.stringify({ type: 'error', message: 'Stream connection lost' })}\n\n`
      );
      res.end();
    });

  } catch (err) {
    console.error('Chat stream proxy error:', err.message);
    const errorMsg =
      err.code === 'ECONNREFUSED'
        ? 'AI Engine is not running'
        : err.response?.status === 401
        ? 'AI Engine authentication failed'
        : `AI Engine error: ${err.message}`;

    res.write(`data: ${JSON.stringify({ type: 'error', message: errorMsg })}\n\n`);
    res.end();
  }
});

export default router;
