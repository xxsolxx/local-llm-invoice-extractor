# local-llm-invoice-extractor

A local, privacy-first ETL pipeline extracting structured financial data from scanned PDF invoices using Tesseract OCR and Ollama (Llama 3.1).

## Overview
This project automates the extraction of financial data from a large dataset of PDF invoices. Since invoices come in various formats—some as text-based PDFs and others as scanned images—this pipeline uses a hybrid approach. It first attempts to extract text directly and falls back to Optical Character Recognition (OCR) if the document is a scanned image. 

Instead of writing highly complex and rigid Regular Expressions for varying invoice layouts, the raw text is processed by a local Large Language Model (LLM) via Ollama. This ensures reliable extraction of structured data while keeping sensitive financial documents 100% locally on the machine, without relying on cloud APIs.

## Features
* **Privacy-First:** 100% local processing using Ollama. No financial data leaves your machine.
* **Hybrid Text Extraction:** Uses `pdfplumber` for native PDFs and `pytesseract` for scanned images.
* **Multi-Language Support:** Configured with Regex filtering to handle both Greek and English characters accurately.
* **Automated Structuring:** LLM parses tangled raw text and outputs structured data ready for Excel/CSV export.

## Prerequisites
Before running this project, you need to install the following external tools:

1. **Tesseract OCR:** Required for reading scanned image PDFs.
   * Windows users can download the installer from the [UB-Mannheim repository](https://github.com/UB-Mannheim/tesseract/wiki).
   * Note the installation path (default is `C:\Program Files\Tesseract-OCR\tesseract.exe`).
2. **Ollama:** Required to run the local LLM.
   * Download and install from [ollama.com](https://ollama.com/).
   * Pull the desired model by running the following command in your terminal: `ollama run llama3.1` (or the specific model you intend to use).

## Installation
1. Clone this repository or download the files.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
