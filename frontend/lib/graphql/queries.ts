import { gql } from '@apollo/client';

export const SEARCH_QUERY = gql`
  query Search($query: String!, $useLlm: Boolean) {
    search(query: $query, use_llm: $useLlm) {
      question
      intent
      intent_confidence
      answer
      sources {
        content
        relevance_score
        metadata {
          section
          act
          chapter
          title
        }
      }
      graph_references {
        case_name
        case_year
        section
        section_title
        act_name
        related_section
        related_title
        relationship
      }
      documents_used
      retrieval_strategy {
        num_documents_requested
        min_relevance_threshold
        num_documents_returned
        intent_reasoning
      }
      confidence
      processing_time_ms
    }
  }
`;
