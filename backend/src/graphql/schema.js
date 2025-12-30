import { gql } from "apollo-server-express";
import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";
import { generateToken } from "../utils/generateToken.js";
import { callAIEngine } from "../services/aiEngineClient.js";

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
  }

  type Source {
    content: String!
    relevance_score: Float!
    metadata: SourceMetadata!
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

  type SearchResult {
    question: String!
    intent: String!
    intent_confidence: Float!
    answer: String!
    sources: [Source]!
    graph_references: [GraphReference]!
    documents_used: Int!
    retrieval_strategy: RetrievalStrategy!
    confidence: Float!
    processing_time_ms: Float!
  }

  type Query {
    getUserProfile(id: ID!): User
    getDocuments: [Document]
    # NEW: AI-powered legal search
    search(query: String!, use_llm: Boolean): SearchResult!
  }

  type Mutation {
    signup(name: String!, email: String!, password: String!): String
    login(email: String!, password: String!): String
  }
`;

export const resolvers = {
  Query: {
    getUserProfile: (_, { id }) => prisma.user.findUnique({ where: { id: Number(id) } }),
    getDocuments: () => prisma.document.findMany(),

    // NEW: AI Engine search resolver
    search: async (_, { query, use_llm = false }) => {
      try {
        const result = await callAIEngine(query, use_llm);
        return result;
      } catch (error) {
        console.error('Search error:', error.message);
        throw new Error(`Search failed: ${error.message}`);
      }
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
  },
};
