code_explain_prompt = """
You are tasked with analyzing a complex legacy PLSQL codebase to generate an English explanation of its business rules 
and logic. This analysis will be used to create requirements documents for redesigning the system in a modern language 
like Java. Your goal is to extract and explain the key elements of the code in a clear, concise manner.

Here is the PLSQL code to analyze:

<plsql_code>
    {PLSQL_CODE}
</plsql_code>

Carefully examine the provided PLSQL code and generate a comprehensive explanation of its functionality, business rules, 
and logic. Your output should be in a bullet point format, organized into the following sections:

1. Overview
   - Name of the script or module.
   - Provide a brief summary of the code's main purpose and functionality.

2. Key Components
   - List and explain the main procedures, functions, and packages in the code.
   - Describe the purpose of each component.

3. Business Rules
   - Identify and explain any business rules implemented in the code.
   - Include conditions, validations, and constraints.

4. Data Flow
   - Describe how data moves through the system.
   - Explain any data transformations or calculations.

5. Error Handling and Exceptions
   - List any error handling mechanisms or custom exceptions.
   - Explain how errors are managed and reported.

6. Database Interactions
   - Describe any database operations (SELECT, INSERT, UPDATE, DELETE).
   - Explain the purpose of these operations in the context of the business logic.

7. Integration Points
   - Identify any external system interactions or API calls.
   - Explain the purpose of these integrations.

8. Performance Considerations
   - Highlight any performance-related code, such as bulk operations or optimizations.

9. Business Logic Summary
   - Provide a concise summary of the overall business logic implemented in the code.

10. Additional Notes
    - Include any observations, potential issues, or recommendations for the redesign process.

When analyzing the code:
- If you encounter complex or unclear sections, provide your best interpretation and note any assumptions made.
- Use clear, non-technical language where possible to explain technical concepts.
- If you identify any potential issues or areas for improvement, include these in your notes.

Remember to focus on extracting the business logic and rules, rather than providing a line-by-line code explanation. 
Your analysis should help developers understand the core functionality and business requirements implemented in this 
PLSQL code, facilitating its redesign in a modern language.

Please also output the word *END* at the end of your response to indicate completion.

"""

java_code_gen_prompt = """

You are a specialized converter for transforming legacy PL/SQL code into a modern Java/Spring Boot microservices architecture using Domain-Driven Design (DDD) principles. Your task is to fully convert the given PL/SQL code into a comprehensive and well-structured Java/Spring Boot application. The output should include all essential components, ensuring a complete codebase with no placeholders or partial code.
You are tasked with generating Java/Spring Boot code from legacy PLSQL code, modernizing it into a architecture using Domain-Driven Design (DDD) concepts. 
Your goal is to create a fully object-oriented codebase that is well-structured and follows best practices for Spring Boot applications. Try to generate the complete code response output.

First, analyze the provided PLSQL code:

<plsql_code>
   {PLSQL_CODE}
</plsql_code>

Follow these steps to convert the PLSQL code to Java/Spring Boot:

1. Identify the main functionalities and data structures in the PLSQL code.
2. Map PLSQL procedures and functions to Java methods.
3. Convert PLSQL data types to appropriate Java data types.
4. Replace PLSQL-specific constructs with Java equivalents.
5. Implement database operations using Spring Data JPA or JDBC Template.
6. Use the Exception handle by PLSQL provide equivalent type in java.

Apply DDD concepts and microservices architecture:

1. Identify bounded contexts within the functionality.
2. Create separate microservices for each bounded context.
3. Define domain entities - Geneate all entites from the plsql code and use lambok, value objects, and aggregates.
4. Implement repositories for data access.
5. Use domain events for communication between microservices.

Organize your code following these guidelines:

1. Use a layered architecture: Controller-Generate all the api service in the code, Service, Repository.
2. Create separate packages for each layer and domain concept.
3. Implement dependency injection using Spring annotations.
4. Use interfaces to define contracts between layers.
5. Apply SOLID principles throughout your code.
6. Provide the complete code genertation for every java classes.
7. Dont give like Other methods for updating, Other endpoints instead of generate complete code.


Conversion Guidelines:

1.  Analyze the Provided PL/SQL Code :
    - Carefully identify key functionalities, database tables, stored procedures, functions, and data structures used in the PL/SQL code.
    - Determine the business logic encapsulated within procedures and functions and translate them into Java methods.

2.  Implement Core Java/Spring Boot Components :
    -  Entity Classes : Generate Java entities that represent the database schema, using JPA annotations. Use Lombok to reduce boilerplate code.
    -  Repositories : Implement Spring Data JPA repositories for each entity to handle data access operations.
    -  Service Layer : Create service classes with clear method mappings for each PL/SQL operation. This includes CRUD operations and any specific business logic.
    -  Controller Layer : Develop REST API endpoints in the controller classes, following RESTful principles and exposing all relevant operations.
    -  Exception Handling : Implement a robust exception handling mechanism, mapping common PL/SQL exceptions to custom Java exceptions, and provide meaningful error messages in the API responses.
    -  Application Configuration : Include a fully-configured `application.properties` file for database connection and other settings.

3.  Apply Domain-Driven Design (DDD) Concepts :
    -  Bounded Contexts : Identify bounded contexts within the business logic and structure the application around these domains, encapsulating related entities, services, and repositories.
    -  Domain Entities and Value Objects : Create value objects and aggregates, utilizing Lombok where applicable to simplify code.
    -  Domain Events : Use domain events to represent changes within entities and facilitate interactions between bounded contexts or other services.

4.  Code Organization :
    - Use a layered package structure: `controller`, `service`, `repository`, `entity`, `exception`, and `config`.
    - Adhere to SOLID principles and use dependency injection to maintain loose coupling across classes.
    - Implement interfaces to define contracts between layers for better modularity.

 Output Requirements:

   - Complete Java Code : Provide the complete implementation for each class, method, and configuration file without placeholders or partial snippets.
   - Code Documentation : Add comments to explain each class, method, and complex logic.
   - Testing: Include basic unit tests for services and controllers to verify functionality.
   - API Documentation : Integrate Swagger or Spring REST Docs for API documentation, if possible.

Format for Response:

The response should include each Java file in the following format:


```java


Package declaration
package com.example.microservice.[layer];

Import statements

Class declarations, including annotations

Method implementations with comments explaining functionality

```

Include comments explaining the purpose of each class and method, especially where complex logic is involved.

Remember to handle errors appropriately and include unit tests for your Java code. Also, consider implementing API 
documentation using Swagger or Spring REST Docs.

Your final output should include multiple Java files representing the different components of the microservices 
architecture, along with a brief explanation of how the code is organized and how it implements the DDD concepts.

Please also output the word *END* at the end of your response to indicate completion.

Instruction for the Generate complete long response output:
   Dont give like Other methods for updating, Other endpoints instead of generate complete code.
   we have more than one LLM calls are availbale. 
   Everytime try to generate the complete code. 
   Dont provide the incomplete code.
   Dont worried about the within token limit try to generate. I need a complete code generate.
   If Incomplete response based on that it will generate the code in next call.
"""

oo_design_prompt = """

You are tasked with modernizing a complex legacy PLSQL codebase to modern Java and Spring Boot microservices. Your goal 
is to generate an object-oriented design from the PLSQL code using Domain-Driven Design (DDD) principles to break the 
design into microservices. You will also create a Mermaid component diagram to visualize the architecture.

Here is the PLSQL code you need to analyze:

<plsql_code>
    {PLSQL_CODE}
</plsql_code>

Follow these steps to complete the task:

1. Analyze the PLSQL code:
   a. Identify the main functionalities and business logic in the code.
   b. Determine the data structures and their relationships.
   c. Recognize any existing modules or logical separations in the code.

2. Apply Domain-Driven Design (DDD) principles:
   a. Identify the core domain and subdomains based on the business logic in the PLSQL code.
   b. Define bounded contexts for each subdomain.
   c. Identify entities, value objects, and aggregates within each bounded context.
   d. Determine the domain events and commands.

3. Design microservices:
   a. Map each bounded context to a potential microservice.
   b. Ensure each microservice has a single responsibility and is loosely coupled.
   c. Define the APIs for each microservice, including endpoints and data contracts.
   d. Identify shared libraries or common functionalities that can be extracted.

4. Create a Mermaid component diagram:
   a. Represent each microservice as a component.
   b. Show the relationships and dependencies between microservices.
   c. Include external systems or databases if applicable.
   d. Use appropriate Mermaid syntax for component diagrams.

5. Provide your output in the following format:
   a. Start with a brief overview of the identified domains and subdomains.
   b. List each microservice with its responsibilities and main entities.
   c. Describe the APIs for each microservice.
   d. Include the Mermaid component diagram code.
   e. Conclude with any additional considerations or recommendations for the modernization process.

Enclose your entire response within <answer> tags. Use appropriate subheadings to organize your response clearly. 
Present the Mermaid diagram code within <mermaid> tags.

Remember to focus on creating a clean, modular design that adheres to DDD principles and microservices architecture 
best practices. Your design should aim to improve maintainability, scalability, and flexibility compared to the original
 PLSQL codebase.
 
Please also output the word *END* at the end of your response to indicate completion.

"""

ms_prompt="""
 
Convert my existing Spring Boot project into a microservices architecture by creating a separate Java Spring microservice for each entity class in the project. Each microservice should include:
 
Given the following Spring Boot code
<Spring_Boot_code >
    {PLSQL_CODE}
</Spring_Boot_code >
Convert each entity in my Spring Boot project (Employee, Book, Video, Card, Rent) into a standalone microservice. For each entity, create an independent Java Spring Boot microservice project with the following structure and requirements:
 
Project Structure:
 
Create a new Spring Boot project for each entity (EmployeeService, BookService, etc.), each as a standalone microservice with its own codebase.
Each microservice should have separate controller, service, and repository packages.
Controller Layer:
 
In each microservice, implement a RESTful controller to handle CRUD operations for that specific entity (EmployeeController, BookController, etc.).
Expose endpoints for creating, retrieving, updating, and deleting the entity, ensuring endpoints follow RESTful naming conventions and return JSON responses.
Service Layer:
 
For each microservice, include a service layer (EmployeeService, BookService, etc.) to encapsulate business logic specific to that entity.
Data Access Layer:
 
Define repository interfaces (EmployeeRepository, BookRepository, etc.) using Spring Data JPA, with CRUD operations for each entity.
Configure each microservice with a separate database connection in application.yml or application.properties, if needed.
Error Handling:
 
Add global exception handling in each microservice to manage common errors (validation, not found, etc.) and return clear HTTP status codes.
Swagger Documentation:
 
Enable Swagger in each microservice to provide documentation for the available API endpoints.
Testing:
 
Write unit tests for service methods and integration tests for controller endpoints in each microservice using JUnit and Mockito.
Independent Packaging and Deployment:
 
Package each microservice as an independent JAR file with an embedded Tomcat server, making it runnable as a standalone service (java -jar <filename>.jar).
Ensure that each microservice can be independently deployed and communicates over HTTP if inter-service calls are required in the future.
After completing this, each entity will have its own self-contained microservice, ready for modular deployment and scalable in a microservices architecture.
 
Instructions:
 
1.Repeat for Other Entities:dont give this message ,instead generate separate microservice
 
"""

ms_doc_prompt="""
 
Convert my existing Spring Boot project into a microservices architecture by creating a separate Java Spring microservice for each entity class in the project. Each microservice should include:
Give is the micoservice documentation. Based on that and spring boot code Generate micorservice with proper connection betweent the service also strictly follow the proper structure.
{response} 
Given the following Spring Boot code
<Spring_Boot_code >
    {PLSQL_CODE}
</Spring_Boot_code >
Convert each entity in my Spring Boot project (Employee, Book, Video, Card, Rent) into a standalone microservice. For each entity, create an independent Java Spring Boot microservice project with the following structure and requirements:
 
Project Structure:
 
Create a new Spring Boot project for each entity (EmployeeService, BookService, etc.), each as a standalone microservice with its own codebase.
Each microservice should have separate controller, service, and repository packages.
Controller Layer:
 
In each microservice, implement a RESTful controller to handle CRUD operations for that specific entity (EmployeeController, BookController, etc.).
Expose endpoints for creating, retrieving, updating, and deleting the entity, ensuring endpoints follow RESTful naming conventions and return JSON responses.
Service Layer:
 
For each microservice, include a service layer (EmployeeService, BookService, etc.) to encapsulate business logic specific to that entity.
Data Access Layer:
 
Define repository interfaces (EmployeeRepository, BookRepository, etc.) using Spring Data JPA, with CRUD operations for each entity.
Configure each microservice with a separate database connection in application.yml or application.properties, if needed.
Error Handling:
 
Add global exception handling in each microservice to manage common errors (validation, not found, etc.) and return clear HTTP status codes.
Swagger Documentation:
 
Enable Swagger in each microservice to provide documentation for the available API endpoints.
Testing:
 
Write unit tests for service methods and integration tests for controller endpoints in each microservice using JUnit and Mockito.
Independent Packaging and Deployment:
 
Package each microservice as an independent JAR file with an embedded Tomcat server, making it runnable as a standalone service (java -jar <filename>.jar).
Ensure that each microservice can be independently deployed and communicates over HTTP if inter-service calls are required in the future.
After completing this, each entity will have its own self-contained microservice, ready for modular deployment and scalable in a microservices architecture.
 
Instructions:
 
1.Repeat for Other Entities:dont give this message ,instead generate separate microservice
 
"""
