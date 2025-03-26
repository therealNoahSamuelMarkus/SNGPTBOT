# SNGPTBOT

**Description of the Project**
This project aims to build a ChatGPT-powered virtual IT service desk agent that integrates directly into a ServiceNow instance. The core goal is to enhance self-service IT support by enabling users to ask natural language questions and receive accurate, context-aware responses based on company-specific knowledge base (KB) articles.

Key Features:

GPT-Powered Conversational Agent: Uses OpenAI's GPT models to interpret and respond to IT support queries in natural language.

ServiceNow KB Integration: Dynamically retrieves relevant articles from the organization’s ServiceNow KB to generate informative responses.

Access-Controlled Responses: Respects article-level access permissions—if a signed-in user lacks access to an article, the agent will neither access nor use its content in its response.

Citations in Responses: The agent cites the knowledge base articles it draws from to promote transparency and trust.

Live in ServiceNow: Designed to live within the ServiceNow platform, appearing as a virtual support assistant available on the portal or via a chat interface.

Innovation & Impact:

Reduces workload for human IT staff by automating responses to repetitive and common queries.

Enhances user experience with fast, conversational support tailored to the company’s actual IT documentation.

Ensures data security by maintaining strict adherence to existing KB access rules.

**Resources to Use**
OpenAI API: For natural language understanding and generation (ChatGPT, GPT-4).

ServiceNow REST API: To query KB articles, user session info, and validate access permissions.

GitHub Repositories:

OpenAI’s official API examples

ServiceNow API integrations

Data Sources:

Internal company knowledge base articles stored in ServiceNow (mock or real data depending on access).

Frameworks and Tools:

Python or JavaScript for the agent logic and API calls.

ServiceNow Studio for platform-side development.

Prior experience from lab assignments involving REST APIs, secure auth, and chatbot frameworks.

**Deliverables**
Live Demo of the chatbot running inside a ServiceNow instance, demonstrating real-time responses and article citation.

GitHub Code Repository with full source code, README documentation, and deployment instructions.
