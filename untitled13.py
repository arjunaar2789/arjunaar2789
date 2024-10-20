# -*- coding: utf-8 -*-
"""Untitled13.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1oAqr0T2aPXJI3FDo6RvquRt3EpK882vz
"""


pip install PyPDF2
pip install sentence_transformers

import streamlit as st
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# Load the summarizer and QA model
summarizer = pipeline('summarization', model='facebook/bart-large-cnn', device=0)
qa_model = pipeline('question-answering', model='deepset/roberta-base-squad2', device=0)

# Initialize the SentenceTransformer model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Streamlit App Layout
st.title("PDF Bot")
st.write("Upload a PDF and ask questions based on its content.")

# PDF Upload
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file is not None:
    # Extract text from PDF
    def extract_text_from_pdf(uploaded_file):
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
        return text

    # Split the extracted text into sections
    def split_into_sections(text, section_length=2000):
        return [text[i:i + section_length] for i in range(0, len(text), section_length)]

    # Process the uploaded PDF
    pdf_text = extract_text_from_pdf(uploaded_file)
    pdf_sections = split_into_sections(pdf_text)

    # Vectorize the sections
    vectorizer = TfidfVectorizer()
    pdf_tfidf_matrix = vectorizer.fit_transform(pdf_sections)
    pdf_embeddings = model.encode(pdf_sections)

    # Show a success message
    st.success("PDF uploaded and processed successfully!")

    # Get the user's question
    query = st.text_input("Enter your question")

    if query:
        # Hybrid retrieval function
        def hybrid_retrieve_pdf(query, pdf_sections, pdf_embeddings, pdf_tfidf_matrix, alpha=0.7, num_sections=5):
            query_embedding = model.encode(query)
            dense_scores = util.cos_sim(query_embedding, pdf_embeddings).flatten()
            sparse_scores = vectorizer.transform([query]).dot(pdf_tfidf_matrix.T).toarray().flatten()
            hybrid_scores = alpha * dense_scores + (1 - alpha) * sparse_scores

            top_indices = hybrid_scores.argsort()[-num_sections:][::-1]
            top_sections = [pdf_sections[i] for i in top_indices]
            return top_sections

        # Retrieve the top sections
        retrieved_sections = hybrid_retrieve_pdf(query, pdf_sections, pdf_embeddings, pdf_tfidf_matrix)

        if retrieved_sections:
            # Combine the retrieved sections
            context = ''.join(retrieved_sections)

            # Generate the answer using the summarizer
            answer = summarizer(context, max_length=150, do_sample=False)
            st.write("Answer: ", answer[0]['summary_text'])
        else:
            st.write("No relevant sections found.")

