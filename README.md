This project showcases a simple Retail Store Agent (Assistant) capable of answering customer questions catering to Store FAQs and questions related to customer's orders using Retrieval Augmented Generation (RAG) and MCP.
A core RAG system that loads internal documents, chunks them intelligently, embeds them into a vector database, retrieves relevant content, and returns it to the agent.
A MCP client connection to a PostgreSQL database hosted on AWS which stores data related to Store's orders including products sold, sales amount and shipping status.
A agent is setup to take the customer query, evaluate and route to the correct tool or MCP and generate grounded answers.
Key Objectives/Goals:
* Understand the building blocks for a multi-tool agentic system which can call inbuilt tools or external MCP servers
* Understand how a end to end RAG system works
* Considerations for prompt building
* Understand how to instantiate and call MCP servers
