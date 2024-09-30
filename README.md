# Real-Time Misinformation Detection in Political Speeches using RAG and Gen AI

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [How It Works](#how-it-works)
  - [Data Collection through Web Scraping](#data-collection-through-web-scraping)
  - [Speech Processing and Speaker Identification](#speech-processing-and-speaker-identification)
  - [Retrieval-Augmented Generation (RAG)](#retrieval-augmented-generation-rag)
  - [Real-Time Misinformation Detection](#real-time-misinformation-detection)
- [Benefits of RAG Implementation](#benefits-of-rag-implementation)
- [Technologies Used](#technologies-used)
- [Flowcharts](#flowcharts)
- [Getting Started](#getting-started)
- [License](#license)

## Introduction

This application leverages **Retrieval-Augmented Generation (RAG)** to detect misinformation in political speeches, rallies, and debates in real-time. By integrating advanced speech-to-text processing, speaker verification, and large language models, the tool provides instant insights into the accuracy of statements made by political figures.

## Features

- **Real-Time Speech Processing and Speaker Diarization**: Converts live video streams or MP4 files into text using WhisperX API.
- **Speaker Verification**: Verifies speakers by creating embeddings of known 2024 political candidates using PyAnnote Audio.
- **Dynamic Data Collection**: Continuously scrapes official websites for new transcripts, press releases, and policy documents.
- **RAG Implementation**: Uses Retrieval-Augmented Generation to compare spoken content against a vector database for misinformation detection.
- **Embeddings and Vector Database**: Stores and retrieves data efficiently using OpenAI Embeddings API and PGVector.
- **Continuous Learning**: Adds new information from video streams into the vector database for future retrieval.

## How It Works
![Drawing1](https://github.com/user-attachments/assets/f7c5b63f-dbcb-4d19-98cb-e1a7b49308e8)

### Data Collection through Web Scraping
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

### Speech Processing and Speaker Identification
![Drawing3](https://github.com/user-attachments/assets/5e3e04aa-f931-4722-b04e-28bb3759afab)

When a video stream or MP4 file is input:

- **WhisperX API** performs speech-to-text conversion and conducts speaker diarization to segment audio by speaker.
- **PyAnnote Audio** creates embeddings Speaker embeddings which are compared against known embeddings of major political candidates for identification.

### Retrieval-Augmented Generation (RAG)
![Drawing4](https://github.com/user-attachments/assets/0779f8f2-d5fb-4904-9b1f-e1a427ff01bb)
As text is generated:

- It is chunked using **LangChain**.
- Embeddings are created and stored in a vector database (**PGVector**).
- The system creates augmented queries to search the vector database for related information.

While the speaker is talking:

- Augmented queries check the vector database to verify the accuracy of statements.
- Results from the large language model (LLM) are integrated back into the database.
- The system provides immediate feedback on whether the speaker is telling the truth.

## Benefits of RAG Implementation

- **Enhanced Accuracy**: RAG combines retrieved data with generative models to produce more factual and context-aware responses.
- **Efficient Retrieval**: Vector databases enable fast and scalable similarity searches, crucial for real-time applications.
- **Dynamic Updating**: Continuously enriches the knowledge base with new data from both web scraping and live inputs.
- **Contextual Understanding**: Provides deeper insights by considering the context around statements, not just isolated facts.
- **Scalability**: Modular design allows for easy expansion to include more speakers or data sources.

## Technologies Used

- **WhisperX API**: For speech-to-text conversion.
- **PyAnnote Audio**: For speaker diarization and verification.
- **LangChain**: For text chunking and processing.
- **OpenAI Embeddings API**: To create embeddings of text data.
- **PGVector**: Vector database for storing embeddings.
- **Scrapy**: Web crawling framework for data collection.
- **Large Language Models (LLMs)**: For generating augmented queries and interpreting results.

## Getting Started

**Prerequisites**:

- Python 3.8 or higher
- API keys for OpenAI and WhisperX
- PostgreSQL database with PGVector extension

**Installation**:

