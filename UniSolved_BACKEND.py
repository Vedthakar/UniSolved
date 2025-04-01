import os
from openai import OpenAI
import psycopg2
import json


client = OpenAI(api_key="OPEN_API_KEY")
def get_db_connection():
    return psycopg2.connect(
        dbname="ai_chatbot",
        user="postgres",
        password="password",
        host="localhost",
        port="5432"
    )
def fetch_articles(keyword):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, authors, abstract, full_text_link
        FROM research_articles
        WHERE keywords ILIKE %s
    """, (f'%{keyword}%',))
    articles = cur.fetchalhl()
    cur.close()
    conn.close()
    return articles

def chat_with_gpt(prompt):
    articles = fetch_articles(prompt)
    
    # Create article context string
    article_context = "\n".join(
        [f"Article {i+1}: {art['title']} by {art['authors']}" 
         for i, art in enumerate(articles)]
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": """You are a university assitant bot.
                    You have access to all of the reasources aviable in a university not just 
                   campus resources but practical ones as well. You want to help uni students with 
                   what ever type of problem they are facing by connecting them to the right recources
                   (wether it is campus resources or connecting them to other people aviable in the database that I will provide later.
                    Make the decision by ranking the reasources in order of what is most optimal in the sceneriao discribed by the user) 
                   and providing a step by step guide to solve issues, and prompting them with follow up questions if needed inorder to 
                   rank the resources and asking any relevant info by referring to the flow chart provided later. 
                   Make sure to use informal diction as if you are a university student.Use the articles below to answer the user's query.
                {article_context}
                - Base your response on the provided research.
                - Cite article numbers (e.g., 'Article 1 states...').
                - If unsure, say 'Based on my research: [summary]'. """}
                  ,{"role": "user", "content": prompt}],
        temperature=1.2,  # More creative
        max_tokens=200,   # meduim responses
        presence_penalty=0.8  # Stay on-topic
    )
    return {
        "response": response.choices[0].message.content,
        "articles": articles,
        "status": "success"
    }

if __name__ == "__main__":
    test_response = chat_with_gpt("test query")
    print(json.dumps(test_response, indent=2))

