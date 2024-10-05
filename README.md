# Real-Time Misinformation Detection in Political Speeches using RAG and Gen AI

## 📑 Table of Contents

- [📘 Introduction](#real-time-misinformation-detection-in-political-speeches-using-rag-and-gen-ai)  
- [✨ Features](#features)  
- [📋 To Do](#to-do)  
- [⚙️ How It Works](#how-it-works)  
    - [🔍 Retrieval-Augmented Generation (RAG)](#retrieval-augmented-generation-rag)  
    - [🗣️ Speech Processing and Speaker Identification](#speech-processing-and-speaker-identification)  
    - [🌐 Data Collection through Web Scraping](#data-collection-through-web-scraping)  
- [🌟 Benefits of RAG Implementation](#benefits-of-rag-implementation)  
- [🛠️ Technologies Used](#technologies-used)  
- [🚀 Getting Started](#getting-started)


# Real-Time Misinformation Detection in Political Speeches using RAG and Gen AI

## 📘 Introduction

This application leverages **Retrieval-Augmented Generation (RAG)** to detect misinformation in political speeches, rallies, and debates in real-time. By integrating advanced speech-to-text processing, speaker verification, and large language models, the tool provides instant insights into the accuracy of statements made by political figures.


## ✨ Features

- **Real-Time Speech Processing and Speaker Diarization**: Converts live video streams or MP4 files into text using WhisperX API.
- **Speaker Verification**: Verifies speakers by creating embeddings of known 2024 political candidates using PyAnnote Audio.
- **Dynamic Data Collection**: Continuously scrapes official websites for new transcripts, press releases, and policy documents.
- **RAG Implementation**: Uses Retrieval-Augmented Generation to compare spoken content against a vector database for misinformation detection.
- **Embeddings and Vector Database**: Stores and retrieves data efficiently using OpenAI Embeddings API and PGVector.
- **Continuous Learning**: Adds new information from video streams into the vector database for future retrieval.

## 📋 To Do
### Backend:
- [x] Refactor Code for Speech-to-text, Media Player & ensure concurancy <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; \:octocat: [refactor-routes branch](https://github.com/nishanthdass/RAG-fact-checker/tree/refactor-routes) <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; \:brain: [Brainstorm.md](https://github.com/nishanthdass/RAG-fact-checker/blob/main/Brainstorm.md)
- [ ] Launch and build out Scrapy server to collect Data for Context retreival
- [ ] Build out Retreival system vectorizes embeddings and store in Vector db
- [ ] Build system for Query Excpansion
- [ ] Formalize and validate Answers


### Frontend:
- [ ] Make Scrollable list for videos
- [ ] Configure processing or loading screen for React-player window
- [ ] Create realtime subtitles output for React-player window
- [ ] Create window to show vectorized data graph
- [ ] Create window to display Query expansions
- [ ] Create window to display Generations

## ⚙️ How It Works

### Overview:
![Drawing1](https://github.com/user-attachments/assets/9e112567-4324-4b1c-8d0e-405f98a9f85a)



### 🔍 Retrieval-Augmented Generation (RAG)
![Drawing4](https://github.com/user-attachments/assets/0779f8f2-d5fb-4904-9b1f-e1a427ff01bb)
As text is generated:

- It is chunked using **LangChain**.
- Embeddings are created and stored in a vector database (**PGVector**).
- The system creates augmented queries to search the vector database for related information.

While the speaker is talking:

- Augmented queries check the vector database to verify the accuracy of statements.
- Results from the large language model (LLM) are integrated back into the database.
- The system provides immediate feedback on whether the speaker is telling the truth.

### 🗣️ Speech Processing and Speaker Identification
![Drawing3](https://github.com/user-attachments/assets/5e3e04aa-f931-4722-b04e-28bb3759afab)

When a video stream or MP4 file is input:

- **WhisperX API** performs speech-to-text conversion and conducts speaker diarization to segment audio by speaker.
- **PyAnnote Audio** creates embeddings Speaker embeddings which are compared against known embeddings of major political candidates for identification.


### 🌐 Data Collection through Web Scraping
![Drawing2](https://github.com/user-attachments/assets/5d2a1ae8-3e95-48c8-8329-3c622bb5601b)

A background server utilizes the **Scrapy** web crawling framework to scrape webpages containing:

- Official transcripts
- Press releases
- Speeches
- Policy documents

The scraped data is:

- Refactored into JSON files.
- Categorized by speaker name and time segments for precise tracking.
- Chunked and stored in a vector database using **LangChain** for optimized retrieval.

## 🌟 Benefits of RAG Implementation

- **Enhanced Accuracy**: RAG combines retrieved data with generative models to produce more factual and context-aware responses.
- **Efficient Retrieval**: Vector databases enable fast and scalable similarity searches, crucial for real-time applications.
- **Dynamic Updating**: Continuously enriches the knowledge base with new data from both web scraping and live inputs.
- **Contextual Understanding**: Provides deeper insights by considering the context around statements, not just isolated facts.
- **Scalability**: Modular design allows for easy expansion to include more speakers or data sources.

## 🛠️ Technologies Used

- **WhisperX API**: For speech-to-text conversion.
- **PyAnnote Audio**: For speaker diarization and verification.
- **LangChain**: For text chunking and processing.
- **OpenAI Embeddings API**: To create embeddings of text data.
- **PGVector**: Vector database for storing embeddings.
- **Scrapy**: Web crawling framework for data collection.
- **Large Language Models (LLMs)**: For generating augmented queries and interpreting results.

## 🚀 Getting Started

## Backend Setup:
Follow these steps to set up the backend of the **RAG Fact Checker** project.

### 1. Clone the Repository

Begin by cloning the project repository to your local machine:

```bash
git clone https://github.com/nishanthdass/RAG-fact-checker
```

### 2. Navigate to the Backend Directory
```bash
cd RAG-fact-checker/backend
```

### 3. Create a Conda Environment
Create a new Conda environment with Python 3.10 for the project:
```bash
conda create --name fact-checker python=3.10
```

### 4. Activate the Conda Environment
Activate the newly created Conda environment:
```bash
conda activate fact-checker
```

### 5. Install the Required Dependencies
Install the project dependencies listed in the requirements.txt file:
```bash
pip install -r requirements.txt
```

### 6. Create the .env File
Create a .env file in the backend directory to store your required keys for authentication. This is necessary for accessing the PyAnnote speaker diarization and embedding models. Your .env file should contain the following keys:

```bash
pipeline=your_pyannote_diarization_token
inference_model=your_pyannote_embedding_token
```

Ensure that you replace your_pyannote_diarization_token and your_pyannote_embedding_token with your actual tokens from PyAnnote.
- pyannote/speaker-diarization-3.1: https://huggingface.co/pyannote/speaker-diarization-3.1
- pyannote/embedding: https://huggingface.co/pyannote/embedding

### 7. Run the Backend Server
To start the backend server, run:
```bash
uvicorn main:app --reload
```

## Frontend Setup:
Follow these steps to set up the frontend of the **RAG Fact Checker** project. Make sure you have cloned the directory.

### 8. Navigate to the Frontend Directory
```bash
cd RAG-fact-checker/frontend
```

### 9. Install packages
```bash
npm install
```

### 10. Start frontend 
```bash
npm start
```
