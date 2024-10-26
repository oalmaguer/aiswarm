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
api_key = st.secrets["general"]["OPENAI_API_KEY"]
model_name = st.secrets["general"]["OPENAI_MODEL_NAME"]

current_date = datetime.now().strftime("%Y-%m")


openai_client = OpenAI(
    api_key = api_key,
)
# initialize swarm
client = Swarm(client=openai_client)

video_files = [
    "assets/robot1.mp4",
    "assets/robot2.mp4",
    "assets/robot3.mp4"
]

#1, create internet search 
#openai implementation
# def get_news_articles(topic):
#     prompt = f"fetch the 7 latest news articles on {topic} as of {current_date}."
#     response = openai_client.chat.completions.create(
#         model='gpt-4o',
#         messages=[{"role": "user", "content": prompt}],
#         max_tokens=500,
#         n=1,
#         stop=None,
#         temperature=0.7,
#     )
#     print(f"response: {response}")
#     return response.choices[0].message.content

#duckduck go implementation
def get_news_articles(topic):
    print(f"Searching for {topic}")
    
    #DUCKDUCKGO SEARCH
    ddg_api = DDGS()
    results = ddg_api.text(f"{topic} after:{current_date}", max_results=5, region='wt-wt', safesearch='moderate', timelimit='7d')
    if results:
        news_articles = "\n\n".join([f"Title: {result['title']}\nLink: {result['href']}\nSnippet: {result['body']}" for result in results])
        print(f"Found {len(results)} results")
        return news_articles
        # transfer_to_editor(news_articles)
    else:
        return f"No results found for {topic}"
    
    
#create ai agents
# News Agent to fetch news
news_agent = Agent(
    name="News Assistant",
    instructions="You provide the latest news articles for a given topic using DuckDuckGo search. Make it short, concise and easy to read. Also add some humour and sarcasm over there.",
    functions=[get_news_articles],
    model='gpt-4o',
)

# Editor Agent to edit news
editor_agent = Agent(
    name="Editor Assistant",
    instructions="Rewrite and give me as news article ready for publishing in an easy to read language. Make it as professional as possible.",
    model='gpt-4o',
)

# COnvert to JSON Agent to edit news
convert_to_json_agent = Agent(
    name="Convert to JSON Assistant",
    instructions="Convert the news article to VALID JSON format. Each News story in separate section. The array will be called `news_articles`. `title`, `link`, `snippet`.",
    model='gpt-4o',
)

current_news = []




#create workflow

def run_news_workflow(topic):
    print('Running news workflow')
    col1, col2, col3 = set_robots()

    with st.spinner(f"The robots are fetching the latest news on {topic}..."):
        #fetch news
        news_response = client.run(
        news_agent,
            [{"role": "user", "content": f"Search the internet for news articles on {topic} after {current_date}"},
            ],
        )

        raw_news = news_response.messages[-1]["content"]


    #transfer to editor
    with st.spinner("The robots are editing the news..."):
        editor_response = client.run(
            agent=editor_agent,
        messages=[{"role": "user", "content": raw_news}],
    )

    with st.spinner("The robots are converting the news to JSON..."):
        json_response = activateJsonAgent(editor_response.messages[-1]['content'])
        
        remove_robots(col1, col2, col3)
        return json_response
  
def remove_robots(col1, col2, col3):
    col1.empty()
    col2.empty()
    col3.empty()

def activateJsonAgent(editor_response):

    json_response = client.run(
        agent=convert_to_json_agent,
        messages=[{"role": "user", "content": editor_response}],
    )

    json_data = json_response.messages[-1]["content"]
    json_data = json_data.strip('` \n')

    if json_data.startswith('json'):
        json_data = json_data[4:]  # Remove the first 4 characters 'json'
        parsed_json = json.loads(json_data)
        return parsed_json["news_articles"]
    
    return json.loads(json_data)

def start_agents(topic):
    json_response = run_news_workflow(topic)
    return json_response



def set_robots():
    col1, col2, col3 = st.columns((3), gap="medium")
    st.header("Robots are working...")

    with col1:
        st.caption("Fetching news...")
        st.image("assets/robot11.gif")

    with col2:
        st.caption("Editing news...")
        st.image("assets/robot22.gif")

    with col3:
        st.caption("Publishing news...")
        st.image("assets/robot33.gif")

    return col1, col2, col3
            




def main():
    st.title("News Fetcher")
    topic = st.text_input("Enter Topic", placeholder="e.g., AI in Mexico")

    if st.button("Fetch News"):
        if topic:
            news_articles = run_news_workflow(topic)
            print(f"news_articles: {news_articles}")
            if isinstance(news_articles, list):
                st.subheader("News Articles:")
                for article in news_articles:
                    st.markdown(f"**Title:** {article['title']}")
                    st.markdown(f"[Read more]({article['link']})")
                    st.markdown(f"*Snippet:* {article['snippet']}")
                    st.markdown("---")
                
            else:
                st.error(news_articles)  # Display error message if no results found
        else:
            st.warning("Please enter a topic.")

if __name__ == "__main__":
    main()