import { gql } from "apollo-server-express";
import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";
import { generateToken } from "../utils/generateToken.js";
import { callAIEngine } from "../services/aiEngineClient.js";
import * as chatService from "../services/chatService.js";

const prisma = new PrismaClient();

export const typeDefs = gql`
  type User {
    id: ID!
    name: String!
    email: String!
  }

  type Document {
    id: ID!
    title: String!
    content: String!
    source: String
  }

  # AI Engine Types
  type SourceMetadata {
    section: String
    act: String
    chapter: String
    title: String
    source: String
    id: String
    rank: Int
  }

  type Source {
    content: String!
    relevance_score: Float!
    metadata: SourceMetadata
  }

  type GraphReference {
    case_name: String
    case_year: Int
    section: String
    section_title: String
    act_name: String
    related_section: String
    related_title: String
    relationship: String
  }

  type RetrievalStrategy {
    num_documents_requested: Int!
    min_relevance_threshold: Float!
    num_documents_returned: Int!
    intent_reasoning: String
  }

  type WebSource {
    title: String
    url: String
    content: String
    web_source: String
  }

  type SearchResult {
    question: String!
    intent: String!
    intent_confidence: Float!
    answer: String!
    sources: [Source]!
    graph_references: [GraphReference]!
    web_sources: [WebSource]!
    documents_used: Int!
    retrieval_strategy: RetrievalStrategy!
    confidence: Float!
    processing_time_ms: Float!
  }

  # Chat Types
  type ChatSession {
    id: ID!
    userId: Int
    title: String
    createdAt: String!
    updatedAt: String!
    messages: [ChatMessage!]!
  }

  type ChatMessage {
    id: ID!
    sessionId: String!
    role: String!
    content: String!
    metadata: String
    createdAt: String!
  }

  type Query {
    getUserProfile(id: ID!): User
    getDocuments: [Document]
    # AI-powered legal search
    search(query: String!, use_llm: Boolean): SearchResult!
    # Chat queries
    getChatSession(sessionId: String!): ChatSession
    getChatSessions(userId: Int): [ChatSession!]!
    getChatHistory(sessionId: String!): [ChatMessage!]!
  }

  type Mutation {
    signup(name: String!, email: String!, password: String!): String
    login(email: String!, password: String!): String
    # Chat mutations
    createChatSession(userId: Int): ChatSession!
    sendMessage(sessionId: String!, message: String!, useLlm: Boolean, useCrew: Boolean): ChatMessage!
    clearChatSession(sessionId: String!): Boolean!
  }
`;

export const resolvers = {
  Query: {
    getUserProfile: (_, { id }) => prisma.user.findUnique({ where: { id: Number(id) } }),
    getDocuments: () => prisma.document.findMany(),

    search: async (_, { query, use_llm = false }) => {
      try {
        const result = await callAIEngine(query, use_llm);
        const transformedSources = (result.sources || []).map(source => ({
          content: source.content || source.excerpt || source.title || 'No content available',
          relevance_score: source.relevance_score || 0.0,
          metadata: source.metadata || {}
        }));
        const transformedGraphRefs = (result.graph_references || []).map(ref => ({
          case_name: ref.case_name || null, case_year: ref.case_year || null,
          section: ref.section || null, section_title: ref.section_title || null,
          act_name: ref.act_name || null, related_section: ref.related_section || null,
          related_title: ref.related_title || null, relationship: ref.relationship || null
        }));
        const transformedWebSources = (result.web_sources || []).map(ws => ({
          title: ws.metadata?.title || 'Untitled', url: ws.metadata?.url || '',
          content: ws.content || '', web_source: ws.metadata?.web_source || 'web'
        }));
        return {
          question: result.question || query, intent: result.intent || 'unknown',
          intent_confidence: result.intent_confidence || 0.0,
          answer: result.answer || 'No answer available',
          sources: transformedSources, graph_references: transformedGraphRefs,
          web_sources: transformedWebSources,
          documents_used: result.documents_used || result.num_sources_retrieved || 0,
          retrieval_strategy: result.retrieval_strategy || {
            num_documents_requested: 0, min_relevance_threshold: 0.0,
            num_documents_returned: 0, intent_reasoning: 'Unknown'
          },
          confidence: result.confidence || 0.0,
          processing_time_ms: result.processing_time_ms || 0.0
        };
      } catch (error) {
        console.error('Search error:', error.message);
        throw new Error(`Search failed: ${error.message}`);
      }
    },

    // ── Chat queries ──────────────────────────────────────────────────────────
    getChatSession: async (_, { sessionId }) => {
      const session = await chatService.getSession(sessionId);
      if (!session) throw new Error('Session not found');
      return {
        ...session,
        createdAt: session.createdAt.toISOString(),
        updatedAt: session.updatedAt.toISOString(),
        messages: session.messages.map(m => ({
          ...m,
          metadata: m.metadata ? JSON.stringify(m.metadata) : null,
          createdAt: m.createdAt.toISOString(),
        })),
      };
    },

    getChatSessions: async (_, { userId }) => {
      const sessions = await chatService.getSessions(userId);
      return sessions.map(s => ({
        ...s,
        createdAt: s.createdAt.toISOString(),
        updatedAt: s.updatedAt.toISOString(),
        messages: (s.messages || []).map(m => ({
          ...m,
          metadata: m.metadata ? JSON.stringify(m.metadata) : null,
          createdAt: m.createdAt.toISOString(),
        })),
      }));
    },

    getChatHistory: async (_, { sessionId }) => {
      const messages = await chatService.getHistory(sessionId);
      return messages.map(m => ({
        ...m,
        metadata: m.metadata ? JSON.stringify(m.metadata) : null,
        createdAt: m.createdAt.toISOString(),
      }));
    },
  },
  Mutation: {
    signup: async (_, { name, email, password }) => {
      const hashed = await bcrypt.hash(password, 10);
      const user = await prisma.user.create({ data: { name, email, password: hashed } });
      return generateToken(user.id);
    },
    login: async (_, { email, password }) => {
      const user = await prisma.user.findUnique({ where: { email } });
      if (!user) throw new Error("Invalid credentials");
      const match = await bcrypt.compare(password, user.password);
      if (!match) throw new Error("Invalid credentials");
      return generateToken(user.id);
    },

    // ── Chat mutations ────────────────────────────────────────────────────────
    createChatSession: async (_, { userId }) => {
      const session = await chatService.createSession(userId);
      return { ...session, messages: [] };
    },

    sendMessage: async (_, { sessionId, message, useLlm = true, useCrew = false }) => {
      // Save user message to DB
      await chatService.saveMessage(sessionId, 'user', message);

      // Call AI Engine
      const aiResult = await chatService.sendToAIEngine(sessionId, message, useLlm, useCrew);

      // Save assistant response to DB — store full sources for rich chat display
      const assistantMsg = await chatService.saveMessage(
        sessionId,
        'assistant',
        aiResult.answer || '',
        {
          intent: aiResult.intent,
          confidence: aiResult.confidence,
          processing_time_ms: aiResult.processing_time_ms,
          sources: aiResult.sources || [],
          graph_references: aiResult.graph_references || [],
          web_sources: aiResult.web_sources || [],
        }
      );

      return {
        ...assistantMsg,
        metadata: JSON.stringify(assistantMsg.metadata),
        createdAt: assistantMsg.createdAt.toISOString(),
      };
    },

    clearChatSession: async (_, { sessionId }) => {
      return chatService.clearSession(sessionId);
    },
  },
};
