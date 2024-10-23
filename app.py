import json
from duckduckgo_search import DDGS
from swarm import Swarm, Agent
from datetime import datetime
from openai import OpenAI
import os
from openai import OpenAI
import gradio as gr
import streamlit as st
import toml

# Load the configuration from the TOML file
# Load environment variables from .env file
# Set your API key here
# Get API key and model name from environment variables
# api_key = os.getenv("OPENAI_API_KEY")
# model_name = os.getenv("OPENAI_MODEL_NAME")
api_key = st.secrets["OPENAI_API_KEY"]
model_name = st.secrets["OPENAI_MODEL_NAME"]
current_date = datetime.now().strftime("%Y-%m")

client = OpenAI(
    api_key = api_key,
)
# initialize swarm
client = Swarm()

#1, create internet search 

def get_news_articles(topic):
    print(f"Searching for {topic}")
    
    #DUCKDUCKGO SEARCH
    ddg_api = DDGS()
    results = ddg_api.text(f"{topic} after:{current_date}", max_results=7)
    if results:
        news_articles = "\n\n".join([f"Title: {result['title']}\nLink: {result['href']}\nSnippet: {result['body']}" for result in results])
        print(f"Found {len(results)} results")
        return news_articles
        # transfer_to_editor(news_articles)
    else:
        return f"No results found for {topic}"
    
    
#create ai agents
# def transfer_to_editor(news_articles):
#     print('Transferring to editor')
#     return editor_agent.run({"role": "system", "content": news_articles})

# News Agent to fetch news
news_agent = Agent(
    name="News Assistant",
    instructions="You provide the latest news articles for a given topic using DuckDuckGo search.",
    functions=[get_news_articles],
    model=model_name
)

# Editor Agent to edit news
editor_agent = Agent(
    name="Editor Assistant",
    instructions="Rewrite and give me as news article ready for publishing in VALID JSON format. Each News story in separate section. The array will be called `news_articles`. `title`, `link`, `snippet`.",
    model=model_name
)



#create workflow

def run_news_workflow(topic):
    print('Running news workflow')

    #fetch news
    news_response = client.run(
        news_agent,
        [{"role": "user", "content": f"Search the internet for news articles on {topic} after {current_date}"}],
    )

    raw_news = news_response.messages[-1]["content"]


    #transfer to editor
    editor_response = client.run(
        agent=editor_agent,
        messages=[{"role": "user", "content": raw_news}],
    )

    json_data = editor_response.messages[-1]["content"]
    json_data = json_data.strip('` \n')

    if json_data.startswith('json'):
        json_data = json_data[4:]  # Remove the first 4 characters 'json'
        parsed_json = json.loads(json_data)
        return parsed_json["news_articles"]

def start_agents(topic):
    editor_response = run_news_workflow(topic)
    print(f"editor_response: {editor_response}")
    return editor_response

def main():
    st.title("News Fetcher")
    topic = st.text_input("Enter Topic", placeholder="e.g., AI in Mexico")
    
    if st.button("Fetch News"):
        if topic:
            with st.spinner("Fetching news..."):
                news_articles = run_news_workflow(topic)
            if isinstance(news_articles, list):
                st.subheader("News Articles:")
                for article in news_articles:
                    st.markdown(f"**Title:** {article['title']}")
                    st.markdown(f"[Read more]({article['link']})")
                    st.markdown(f"*Snippet:* {article['snippet']}")
                    st.markdown("---")
                st.success("Done!")
            else:
                st.error(news_articles)  # Display error message if no results found
        else:
            st.warning("Please enter a topic.")

if __name__ == "__main__":
    main()