import json
import re
import string

from typing import List

from configparser import ConfigParser

from transformers import pipeline

import requests
from bs4 import BeautifulSoup

from google.cloud import storage

from hook.log_setup import get_logger
logger = get_logger(__name__)


class BlogFactory:

    def __init__(self, config: ConfigParser):
        self.config = config

    def create_blog_post(self):
        """
        1) Scrape the web for topics
        2) Pass the topics to GPT-neo for content generation
        3) Upload the content to a JSON file in Google Cloud Storage
        """
        topics: List[dict] = self._find_topics()
        content: List[dict] = self._generate_content(topic_list=topics)
        self._upload_content(content_list=content)

    def _find_topics(self) -> List[dict]:
        """
        Find topics using google search news
        """
        query_string = f"https://www.google.com/search?q={self.config.get('General', 'topic_query')}&tbm=nws"
        content = requests.get(
            query_string)\
            .content
        soup: BeautifulSoup = BeautifulSoup(content, 'html.parser')
        topics = soup.find_all('div', 'BNeawe vvjwJb AP7Wnd')

        if len(topics) == 0:
            raise Exception(f'No topics available for query {query_string}')

        topic_list = []
        for topic in topics:
            # Find the link to the original article
            original_link = topic.find_parent('a').get('href')
            original_link = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[^&]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                                       original_link)[0]
            topic_list.append({
                'title': f"{topic.text}",
                'link': original_link
            })
        return topic_list

    def _generate_content(self, topic_list: List[dict], desired_length: int = 5000) -> List[dict]:
        """
        This function accepts topics and generates fake blog content for those topics.
        """

        # Set the desired length of the content.
        dl = self.config.getint('General', 'desired_length')
        if dl:
            desired_length = dl

        generator = pipeline('text-generation', model='EleutherAI/gpt-j-6B')
        content_list = []
        for topic in topic_list[:self.config.getint('General', 'post_count')]:
            content = generator(topic['title'],
                                do_sample=True,
                                min_length=64,
                                max_length=self.config.getint('General', 'max_seq_length'))[0]['generated_text']
            while len(content) < desired_length:
                content += generator(content[-self.config.getint('General', 'max_seq_length'):],
                                     do_sample=True,
                                     min_length=64,
                                     max_length=self.config.getint('General', 'max_seq_length'))[0]['generated_text'][
                           -self.config.getint('General', 'max_seq_length'):]
            content = re.findall('(.+[.!?])', content, re.DOTALL)[0]
            content_dictionary = {
                'title': topic['title'],
                'link': topic['link'],
                'content': content
            }
            logger.info(content_dictionary)
            content_list.append(content_dictionary)
        return content_list

    def _upload_content(self, content_list: List[dict]) -> None:
        """
        This function is going to upload the blog contents to Google Cloud Storage as a JSON file.
        """
        client = storage.Client()
        bucket = client.get_bucket(self.config.get('General', 'bucket_id'))
        for content in content_list:
            file_name = content['title'].translate(str.maketrans('', '', string.punctuation))
            blob = bucket.blob(f'automated_blog/{file_name}.json')

            # Convert the dictionary to JSON for file upload
            content_str = json.dumps(content)
            blob.upload_from_string(data=content_str,
                                    content_type='application/json')
