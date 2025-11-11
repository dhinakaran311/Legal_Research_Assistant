import { gql } from "apollo-server-express";
import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";
import { generateToken } from "../utils/generateToken.js";

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

  type Query {
    getUserProfile(id: ID!): User
    getDocuments: [Document]
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
