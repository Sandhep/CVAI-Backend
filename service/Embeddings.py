from transformers import BertModel, BertTokenizer
import torch
import spacy # type: ignore
import re
import pandas as pd
from sentence_transformers import SentenceTransformer # type: ignore
import numpy as np
import faiss # type: ignore
nlp = spacy.load('en_core_web_sm')

model = SentenceTransformer('all-MiniLM-L6-v2')

class Embeddings:

    def preProcess(text):
        text = re.sub(r'[^\w\s]', '', text) 
        doc = nlp(str(text))
        preprocessed_text = []
        for token in doc:
            if token.is_punct or token.like_num or token.is_space:
                continue
            preprocessed_text.append(token.lemma_.lower().strip())
        return ' '.join(preprocessed_text)

    def generateBertEmbedding(text, tokenizer, model):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        return embedding


    def processText(input_text):
        cleaned_text = re.sub(r'[^A-Za-z\s]', '', input_text)
        
        words = cleaned_text.split()
        
        processed_words = [word.capitalize() if word.isupper() else word for word in words]
        
        return ' '.join(processed_words)
