/**
 * AI Engine Client - Backend → FastAPI Communication
 * Handles HTTP requests to AI Engine with API key authentication
 */
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const AI_ENGINE_URL = process.env.AI_ENGINE_URL || 'http://localhost:5000';
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

/**
 * Call AI Engine adaptive query endpoint
 * @param {string} query - User's legal question
 * @param {boolean} useLLM - Whether to use LLM for answer generation
 * @returns {Promise<Object>} AI Engine response with answer, sources, graph_references
 */
export async function callAIEngine(query, useLLM = false) {
    if (!INTERNAL_API_KEY) {
        throw new Error('INTERNAL_API_KEY not configured in backend .env');
    }

    try {
        console.log(`🔄 Calling AI Engine: ${query} (LLM: ${useLLM})`);

        const response = await axios.post(
            `${AI_ENGINE_URL}/api/adaptive-query`,
            {
                question: query,
                use_llm: useLLM
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Internal-API-Key': INTERNAL_API_KEY
                },
                timeout: 60000 // 60 seconds (LLM can be slow)
            }
        );

        console.log(`✅ AI Engine response received (${response.data.processing_time_ms}ms)`);
        return response.data;

    } catch (error) {
        console.error('❌ AI Engine call failed:', error.message);

        if (error.response) {
            // AI Engine returned an error response
            const status = error.response.status;
            const detail = error.response.data?.detail || 'Unknown error';

            if (status === 401) {
                throw new Error('AI Engine authentication failed - check INTERNAL_API_KEY');
            } else if (status === 404) {
                throw new Error('AI Engine endpoint not found - check AI_ENGINE_URL');
            } else {
                throw new Error(`AI Engine error (${status}): ${detail}`);
            }
        } else if (error.code === 'ECONNREFUSED') {
            throw new Error('AI Engine is not running - start it at ' + AI_ENGINE_URL);
        } else if (error.code === 'ETIMEDOUT') {
            throw new Error('AI Engine request timeout - query took too long');
        } else {
            throw new Error('Failed to connect to AI Engine: ' + error.message);
        }
    }
}

/**
 * Health check for AI Engine
 * @returns {Promise<boolean>} True if AI Engine is healthy
 */
export async function checkAIEngineHealth() {
    try {
        const response = await axios.get(`${AI_ENGINE_URL}/health`, {
            timeout: 5000
        });
        return response.status === 200;
    } catch (error) {
        return false;
    }
}
