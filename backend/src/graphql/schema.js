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
        
        // Transform sources to match GraphQL schema
        // AI Engine returns: {id, title, excerpt, relevance_score, metadata, rank}
        // GraphQL expects: {content, relevance_score, metadata}
        const transformedSources = (result.sources || []).map(source => ({
          content: source.content || source.excerpt || source.title || 'No content available',
          relevance_score: source.relevance_score || 0.0,
          metadata: source.metadata || {}
        }));
        
        // Transform graph_references if needed (handle empty or null)
        const transformedGraphRefs = (result.graph_references || []).map(ref => ({
          case_name: ref.case_name || null,
          case_year: ref.case_year || null,
          section: ref.section || null,
          section_title: ref.section_title || null,
          act_name: ref.act_name || null,
          related_section: ref.related_section || null,
          related_title: ref.related_title || null,
          relationship: ref.relationship || null
        }));
        
        // Return transformed result
        return {
          question: result.question || query,
          intent: result.intent || 'unknown',
          intent_confidence: result.intent_confidence || 0.0,
          answer: result.answer || 'No answer available',
          sources: transformedSources,
          graph_references: transformedGraphRefs,
          documents_used: result.documents_used || result.num_sources_retrieved || 0,
          retrieval_strategy: result.retrieval_strategy || {
            num_documents_requested: 0,
            min_relevance_threshold: 0.0,
            num_documents_returned: 0,
            intent_reasoning: 'Unknown'
          },
          confidence: result.confidence || 0.0,
          processing_time_ms: result.processing_time_ms || 0.0
        };
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
