#Filepath relative the project root[.]: ./src/services/newsapi_service.py
import ast

from dotenv import load_dotenv
from eventregistry import *

from core.databus import global_vars
from core.services.logger_service import LoggerService

load_dotenv()


class NewsApiService:

    def __init__(self):
        self.key = global_vars.NEWSAPI_API_KEY
        # Initialize API client

    def get_fresh_headlines_by_topic(self, first_parameter, second_parameter, connector_id, max_results):
        er = EventRegistry(apiKey=self.key, verboseOutput=True, allowUseOfArchive=False)

        logger = LoggerService()
        # get the USA URI
        # local_server = er.getLocationUri("")  # = http://en.wikipedia.org/wiki/United_States

        keywords = first_parameter
        logger.info('[NewsApiService::get_fresh_headlines_by_topic] keywords: ' + keywords)
        # logger.info(f"local_server: " + str(local_server))
        keywords_list = keywords.split(';')

        q = QueryArticlesIter(
            keywords=QueryItems.OR(keywords_list),
            minSentiment=0.4,
            dataType=["news", "blog"]
        )

        search_results = q.execQuery(er, sortBy="date", maxItems=max_results)
        articles_list = [article for article in search_results]

        logger.info(f"max_Results = {max_results}")
        logger.info(f"total results = {len(articles_list)}")

        article_list_filtered = []
        for article in search_results:
            article_list_filtered.append({
                "title": article["title"],
                "description": article["description"],
                "source": article["source"]["title"],
                "date": article["date"]
            })

        return articles_list


def trim_non_alphanumeric(s):
    if not isinstance(s, (str, bytes)):
        raise TypeError("Expected string or bytes-like object")
    # Define a regular expression pattern that matches any character that is not a letter, number, apostrophe, hyphen, space, colon, or double quote
    pattern = re.compile(r"[^a-zA-Z0-9' \-:\"']+")
    # Replace all matched characters with an empty string
    return pattern.sub('', s)


def extract_string_from_list(input_string):

    try:
        list_of_lists = ast.literal_eval(input_string)
    except (ValueError, SyntaxError):
        raise ValueError("Input string is not a valid list representation")

    # Check if the result is a list of lists
    if isinstance(input_string, list) and all(isinstance(i, list) for i in list_of_lists):
        # Flatten the list and join the elements into a single string
        flat_list = [item for sublist in list_of_lists for item in sublist]
        result_string = ' '.join(flat_list)
        return result_string
    else:
        raise ValueError("Input string is not a list of lists")
