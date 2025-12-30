import express from "express";
import { ApolloServer } from "apollo-server-express";
import { typeDefs, resolvers } from "./graphql/schema.js";
import cors from "cors";
import dotenv from "dotenv";

// Import REST routes
import authRoutes from "./api/auth.js";
import feedbackRoutes from "./api/feedback.js";

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();

// Apply CORS
app.use(cors());

// REST API Routes (before GraphQL body parser)
app.use("/api/auth", express.json());
app.use("/api/auth", authRoutes);
app.use("/api/feedback", express.json());
app.use("/api/feedback", feedbackRoutes);

// Apollo Server setup
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => {
    // Get the user token from the headers
    const token = req.headers.authorization || '';
    return { token };
  }
});

// Apply Apollo Server middleware
async function startServer() {
  await server.start();

  // Apply Apollo GraphQL middleware - Apollo handles its own body parsing
  server.applyMiddleware({
    app,
    path: "/graphql",
    cors: false // We're already using CORS middleware
  });

  const PORT = process.env.PORT || 4000;

  app.listen(PORT, () => {
    console.log("====================================");
    console.log(`✅ REST API running at: http://localhost:${PORT}`);
    console.log(`🚀 GraphQL ready at:  http://localhost:${PORT}${server.graphqlPath}`);
    console.log("====================================");
  });
}

// Start the server
startServer().catch(error => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
