# Active Context

## Current Work Focus

- Populating the Memory Bank with details about the "groupdebating" project.

## Recent Changes

- Created the core Memory Bank files: `projectbrief.md`, `productContext.md`, `activeContext.md`, `systemPatterns.md`, `techContext.md`, and `progress.md`.
- Populated `projectbrief.md` and `productContext.md` with project details.

## Next Steps

- Populate the remaining Memory Bank files: `systemPatterns.md`, `techContext.md`, and `progress.md`.

## Active Decisions and Considerations

- Deciding on the appropriate level of detail to include in each Memory Bank file.
- Balancing information from the chatbot and debate simulator components of the project.

## Important Patterns and Preferences

- Using `write_to_file` as a fallback when `replace_in_file` fails due to exact match issues.

## Learnings and Project Insights

- The project consists of two distinct but related Streamlit applications: a chatbot and a debate simulator.
- The chatbot focuses on individual debater Q&A, while the simulator orchestrates debates between multiple debaters using LangGraph.
- Both applications rely on Pinecone for knowledge storage and retrieval, and Google Generative AI for LLM capabilities.
