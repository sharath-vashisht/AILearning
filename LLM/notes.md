# Notes:

Course details:
	- AI Engineer core track by Ed Donnen
	- [https://www.udemy.com/course/llm-engineering-master-ai-and-large-language-models/learn/lecture/52932255#overview](https://www.udemy.com/course/llm-engineering-master-ai-and-large-language-models/learn/lecture/52932255#overview)
	- This is a 8 week course in which Ed will teach on how to develop applications using LLM
	- We will be learning about LLM, RAG, OLoRa and agent
	- We will also be developing several practical application during the course.
	- Github: [https://github.com/ed-donner/llm_engineering](https://github.com/ed-donner/llm_engineering)

Day 1:
	- There are two types of AI models
		○ Frontier models ex: GPT-Model, Claude, Gemini
		○ Open source models ex: Llama, oLLama
	- This course will help us in connecting to both these models.
	- You can download ollama from their website and create a locally running model.
	- Tools needed:
		○ We need to install Cursor
			§ Cursor is an IDE which is generally used for model development
			§ It has lot of AI capabilities
			§ It is fork of VS code, it is not mandatory to use cursor but the recommended approach
			§ It also has command line tool. 
				□ Cursor run  will download and run the model locally.  
		○ We need to install UV  
			§ UV is alternative to anaconda  
			§ It is much more faster compared to anaconda  
			§ It installs all the required packages.  
			§ Package has to be defined in environment.yaml file  
			§ UV sync command will download all the packages and installs it from pyproject.toml file environment.yaml file.  
			§ UV command will also create virtual environment for us to run python code.  
		○ We need a model  
			§ There are two options  
				□ Using frontier models  
					® Generally requires api key to be generated.  
					® For chatgpt we need to go to [https://platform.openai.com/settings/organization/api-keys](https://platform.openai.com/settings/organization/api-keys) and create the key
					® The same key should be stored in .env file in our project.
					® Python has utilities in os packages which can read this .env files.
					® Key has to be OPENAI_API_KEY
					® Similarly other frontier model provides different keys.
				□ Using open source models
					□ It is possible to connect to locally installed ollama to do the job.
					□ How to do will be added later.
		○ Start developing.
	- Open AI APIs:
		○ There are two types of prompts
			§ System prompts
				□ System prompts tell the system how to behave. For example, we can give instructions like give response in funny way.
			§ User prompts
				□ User prompts is the actual question which we need to ask. This will be answered based on how we have told system to behave in system prompts.
			
			[
			    {"role": "system", "content": "system message goes here"},
			    {"role": "user", "content": "user message goes here"}
			]
		® Sample prompt code
		
		openai = OpenAI()
		
		response = openai.chat.completions.create(model="gpt-5-nano", messages=messages)
		
		response.choices[0].message.content

Day 2:
	- Three dimensions of LLM engineering
		® Models
			§ Open source model
				□ Llama from meta
				□ Mistral from Mistral
				□ Qwen from Alibaba cloud
				□ Gemma from Google
				□ Phi from microsoft
				□ Deepseek from deepseek.ai
				□ GPT_OSS from Open AI
			§ Closed source / Frontier model
				□ GPT from open AI
				□ Gemini from Google
				□ Claude from Anthropic
					□ Haiku -> small
					□ Sonnet -> Medium
					□ Opus -> Bing
				□ Grok from X.ai
				□ Others like perplexity, Mistral
			§ Multi-modal
			§ Architecture selection
		® Tools
			§ Hugging face
			§ Longchain
			§ N8n
		® Techniques
			§ APIs
			§ Multishot prompts
			§ RAGs
			§ Fine tuning
			§ Agentization
	- Three ways of using model
		® Using packaged products like chatgpt for GPT
		® Using APIs
			§ By coding ourselves
			§ Consuming via Langchain/n8n
			§ Managed via cloud services
				□ Amazon bedrock
				□ Google Vertex
				□ Azure MCP
		® Download the code and run locally
			§ Hugging face
			§ oLlama
	- Open AI end point was so popular, every LLM started creating API similar to Open AI. 
	- Later Open AI also made that their API can be used to call other LLMs.

Day 3:
	- LLMs comes in 3 variant
		® Base
			§ Old models like GPT-3
		® Chat/Instruct
			§ Newer models
			§ This supports both user and system roles
		® Reasoning/Thinking
			§ Models think before it responds
			§ Chain of thought can be established by asking model to think
	- Most of the current model are hybrid which switches between chat/Instruct to Reasoning/Thinking

### Day 4:

- LLM APIs are stateless
- We need to pass complete conversation to create "Illusion of Memory"
- Input should fit all token in "Context Window"
- There is a new role called Assistant through which we can tell LLM what was the response from Assitant.

