# Meta Ally Standalone Project

## What is the idea behind a Meta Ally?

At the current stage, setting up a **Copilot** on our **configuration page** can be somewhat user-unfriendly and requires prior training or experience. For example, a layperson may struggle to understand why a **RAG** system is needed when building a copilot and what such a system is capable of.  

Even when a user does understand these things, creating and configuring a Copilot still involves **multiple complex steps** specific to our configuration page. These steps include:

- Creating an endpoint with **metadata**, such as a display name and route.  
- Configuring the endpoint by defining a **specific LLM**, **system prompt**, **greeting message**, **history reduction**, and **plugins**.  
- Defining **plugin configuration**, including **AI Knowledge**.  
- (Optional but common) Setting up **AI Knowledge**, which includes:
  - Creating one or more **sources**  
  - Combining sources into a **collection**  
  - **Indexing** the collection  
  - Configuring the plugin within the **copilot configuration**

![Meta Ally overview](docs/Images/image.png)

The goal of the Meta Ally is to integrate all these steps and assist users in creating and configuring their own copilots easily.

The Meta Ally should behave like an autonomous agent that can actively create and configure new endpoints with all required features while **explaining** each concept to the user along the way.

This project aims to improve the usability of Ally’s configuration process. As a side effect, it also explores existing agent frameworks and may help improve the Ally project’s codebase.

---

## What has been done so far?

The initial idea for the **Meta Ally** was to **extend** the functionality of the original **Ally** and use it as its foundation.

When I began my internship in September, I started by exploring the Ally repository.  
One clear **bottleneck** I found was the **lack of flexibility** when introducing new **LLMs** or providers.  
A possible solution was to **migrate** the project to an existing framework such as **LangChain** or **Pydantic AI**.

During exploration, I tried integrating a new DialogEngine based on these frameworks but soon realized that, due to the project’s complexity, adding one at its core would yield **minimal benefits**.

After discussions with Max, we decided the best path forward was to develop a **standalone version** of Ally using a modern framework at its core.

After researching frameworks, I found that **Pydantic AI**, with its type-safe design and extensive documentation, would be an excellent fit.

---

## Tools

A defining feature of an agent is its ability to use **tools**. To enable the Meta Ally to assist users in creating copilots and configuring AI Knowledge sources and collections, it requires a robust toolbox.

I began by turning the respective **Ally** and **AI Knowledge** APIs into Pydantic AI–compatible tools.  
Since the APIs were generated using Pydantic models, it was relatively straightforward to generate tool definitions and parameter descriptions that could be fed to the agent.

However, it still required considerable effort—particularly when converting API operations into callable functions, such as **recursively resolving nested Pydantic models** within request bodies.

![API tools diagram](docs/Images/image-1.png)
![Tool definition example](docs/Images/image-2.png)

---

## Agents

Once the tools were defined, I started creating agents and testing whether tool calls worked correctly.  
Pydantic AI’s built-in **ReAct** agent implementation is simple to use.  

I developed an **agent factory** that allows easy creation of agents by specifying:
- A **prompt**
- A curated **set of tools** selected from the available API tools

---

## UI

To interact with an agent, we can:
- Define static messages in code  
- Or use a frontend interface in the browser  

Pydantic AI supports conversion of your agent into an **AG-UI–based web application**, which can be connected to any frontend implementing the AG-UI protocol.  
In my example, I used **CopilotKit** as the frontend interface.
While this works, it is still feature incomplete for example Human Approval is missing. The issue here is that the AG-UI offers no native support for this and pydantic-ai does not offer a work around.

If needed, one would have to implement a frontend themselves and handle DeferredToolRequests from there.

---

## Evaluation

Evaluating an agent’s performance is crucial.  
Pydantic AI provides a method for evaluation based on **cases**, **tasks**, and **evaluators**.  
However, because this method isn’t restricted to their own agent implementation, I defined a custom evaluation procedure.

I chose to evaluate **message histories**, allowing multi-turn conversation performance assessment.  
I created datasets for specific user profiles to simulate full conversations.  
At several points, I captured **cases** representing conversation snapshots used to measure agent performance.

Evaluations were conducted using both **LLM Judges** and custom evaluators—for instance, comparing expected versus actual tool usage.

---

## Logfire

**Logfire** is Pydantic’s built-in observability platform. It collects traces from your LLM application and sends them to their server, where you can inspect performance metrics through a web dashboard.

You can also review evaluation experiments and their outcomes via Logfire:

![Logfire evaluation view](docs/Images/image-3.png)

---

## Limitations

- No working **Human-in-the-Loop** or **Tool Approval** process yet  
- Evaluation setup is still immature — needs support for executing setup and teardown functions before and after specific cases

---
