from repository.firebase.Firebase import Firebase

from service.Embeddings import Embeddings,model

from service.Summarizer import Summarizer

from service.LLMScore import LLMScore

from fastapi import UploadFile,HTTPException

from firebase_admin import db

import PyPDF2

import faiss

import numpy as np

import pandas as pd

import os

import re

class FileProcess:
    
    async def cvProcess(file):

       text = FileProcess.extractText(file)
       text =  Embeddings.processText(text)
       summary = Summarizer.summarize(text)
       cvUrl = await Firebase.uploadFile(file,'CVs')
       processedcvUrl = await Firebase.uploadText(text, 'processed_resume', file.filename.replace('.pdf', '.txt'))
       summarycvUrl = await Firebase.uploadText(summary, 'summary_resume', file.filename.replace('.pdf', '.txt'))

       return ({
           "cvUrl":cvUrl,
           "processedcvUrl":processedcvUrl,
           "summarycvUrl":summarycvUrl
       })

    async def jdProcess(file): 
       
       text = FileProcess.extractText(file)
       text =  Embeddings.processText(text)
       summary = Summarizer.summarize(text)
       jdUrl = await Firebase.uploadFile(file,'JobDescription')
       processedjdUrl = await Firebase.uploadText(text, 'processed_jd', file.filename.replace('.pdf', '.txt'))
       summaryjdUrl = await Firebase.uploadText(summary, 'summary_jd', file.filename.replace('.pdf', '.txt'))

       return ({
           "jdUrl":jdUrl,
           "processedjdUrl":processedjdUrl,
           "summaryjdUrl":summaryjdUrl
       })
    
    async def fetchCV():
        
        cvs = await Firebase.listFiles("CVs")  
        if not cvs:
            raise HTTPException(status_code=404, detail="No CVs found.")

        response = []
        for name, url in cvs:
            file_name = os.path.splitext(name)[0]
            summary = await Firebase.downloadTextfile(os.getenv("FIREBASE_STORAGE_BUCKET"), f"summary_resume/{file_name}.txt")
            summary_preview = summary[:150] + "..."
            response.append({"name": file_name, "summary": summary_preview, "url": url})

        return response
    
    async def fetchJD():
        
        jds = await Firebase.listFiles("JobDescription")  
        if not jds:
            raise HTTPException(status_code=404, detail="No JDs found.")

        response = []
        for name, url in jds:
            file_name = os.path.splitext(name)[0]
            summary = await Firebase.downloadTextfile(os.getenv("FIREBASE_STORAGE_BUCKET"), f"summary_jd/{file_name}.txt")
            summary_preview = summary[:150] + "..."
            response.append({"name": file_name, "summary": summary_preview, "url": url})

        return response
    
    async def findMatchingCV(selected_jd,top_n,model):
        
        jd_file = os.path.splitext(selected_jd)[0]
        jd_content = await Firebase.downloadTextfile(os.getenv("FIREBASE_STORAGE_BUCKET"), f"processed_jd/{jd_file}.txt")

        # Process resumes
        resumes_list = await Firebase.listFiles("CVs")
        resume_data = []
        for name, url in resumes_list:
            file_name = os.path.splitext(name)[0]
            resume_content = await Firebase.downloadTextfile(os.getenv("FIREBASE_STORAGE_BUCKET"), f"processed_resume/{file_name}.txt")
            resume_data.append({"Filename": file_name, "Content": resume_content, "URL": url})

        if model == "Cosine Similarity":
            # Embed JD
            jd_embed = FileProcess.jdEmbedding(jd_content)

            # Embed resumes and calculate similarity
            df = pd.DataFrame(resume_data)
            index = FileProcess.resumeEmbedding(df)
            distances, indices = index.search(np.array([jd_embed]), top_n)

            # Add similarity scores to the top resumes
            similarity_scores = list(distances[0])
            top_resumes = df.iloc[indices[0]].reset_index(drop=True)
            top_resumes["Score"] = similarity_scores

        elif model == "Gemini-Score":
            top_resumes = await FileProcess.get_match_scores_for_jd(jd_file, resumes_list, "Gemini")

        elif model == "OpenAI-Score":
            top_resumes = await FileProcess.get_match_scores_for_jd(jd_file, resumes_list, "OpenAI")

        elif model == "Claude-Score":
            top_resumes = await FileProcess.get_match_scores_for_jd(jd_file, resumes_list, "Claude")

        else:
            raise HTTPException(status_code=400, detail="Invalid model selected")

        # Format response
        results = []
        for _, row in top_resumes.iterrows():
            results.append({
                "name": row["Filename"],
                "summary": row["Content"][:150] + "...",
                "score": row.get("Score", None),
                "url": row["URL"]
            })

        return {"matches": results}


    def extractText(file: UploadFile)-> str:
            
            pdf_reader = PyPDF2.PdfReader(file.file)
            text = ""

            # Extract text from each page
            for page in pdf_reader.pages:
               text += page.extract_text() or ""  # Use empty string if None is returned

            return text
    
    def resumeEmbedding(df):
         
         df['preprocessed_content'] = df['Content'].apply(Embeddings.preProcess)
         df['resume_embedding'] = df['preprocessed_content'].apply(lambda x: model.encode(x, convert_to_numpy=True))
         resume_embeddings = np.vstack(df['resume_embedding'].values)
         embedding_dim = resume_embeddings.shape[1]
         index = faiss.IndexFlatIP(embedding_dim)  
         index.add(resume_embeddings) 
         return index
   
    def jdEmbedding(job_description):
         
         job_description_text = Embeddings.preProcess(job_description)
         job_description_embedding = model.encode(job_description_text, convert_to_numpy=True)
         return job_description_embedding
    
    async def get_match_score(jd_filename, resume_filename, model):
         
         cache_key = f"{jd_filename}_{resume_filename}_{model}"
         cache_key = FileProcess.sanitize_firebase_path(cache_key)
         ref = db.reference(f"api_scores/{cache_key}")
         cached_score = ref.get() 
         if cached_score:
            return cached_score 
         else:
            jd_content = await Firebase.downloadTextfile(os.getenv("FIREBASE_STORAGE_BUCKET"), f"processed_jd/{os.path.splitext(jd_filename)[0]}.txt")
            resume_content = await Firebase.downloadTextfile(os.getenv("FIREBASE_STORAGE_BUCKET"), f"processed_resume/{os.path.splitext(resume_filename)[0]}.txt")
            
            score = await LLMScore.query_api(model, jd_content, resume_content)
            
            ref.set(score)  
            
            return score 
         
    async def get_match_scores_for_jd(jd_filename, all_resumes, model):
         
         scores = {}  
         for resume_filename, resume_url in all_resumes:
            score = await FileProcess.get_match_score(jd_filename, resume_filename, model)
            scores[resume_filename] = (float(score), resume_url)
         
         sorted_scores = sorted(scores.items(), key=lambda item: item[1][0], reverse=True)

         df_scores = pd.DataFrame(
            [(filename, score[0], score[1]) for filename, score in sorted_scores], 
            columns=['Filename', 'Score', 'URL']
         )
         
         df_scores.to_csv("sample.csv")
         return df_scores
    
    def sanitize_firebase_path(path):
    
        path = path.replace(" ", "_")
        sanitized_path = re.sub(r'[.#$[\]]', '_', path)
        return sanitized_path