#Filepath relative the core root[.]: ./loopai_src/core/services/technews_service.py
import ast

from dotenv import load_dotenv
from eventregistry import *
import feedparser

from core.databus import global_vars
from core.services.logger_service import LoggerService

from web.routes.filesystem import logger_service

load_dotenv()

rss_feeds = {
    'ai': [
        'https://www.technologyreview.com/feed/', # MIT Tech Review
        'https://arstechnica.com/gadgets/feed/', # Ars Technica - Gadgets & AI
        'https://www.wired.com/feed/category/science/', # Wired - Science (AI-related news)
        'https://feeds.feedburner.com/oreilly/radar', # O'Reilly Radar - AI & emerging tech
        'https://thenextweb.com/feed/', # The Next Web (AI section)
        'https://www.forbes.com/ai/feed/', # Forbes AI
        'https://venturebeat.com/category/ai/feed/', # VentureBeat - AI section
        'https://feeds.feedburner.com/udacity-ai', # Udacity AI Blog
        'https://spectrum.ieee.org/rss/artificial-intelligence', # IEEE Spectrum - AI section
        'https://www.datasciencecentral.com/main/rss.xml', # Data Science Central (AI and data science)
        'https://feeds.feedburner.com/Synced', # Synced AI News
    ],
    'e_commerce': [
        'https://techcrunch.com/tag/ecommerce/feed/', # TechCrunch - e-commerce
        'https://www.forbes.com/business/feed/', # Forbes Business
        'https://feeds.feedburner.com/PracticalEcommerce', # Practical Ecommerce
        'https://www.digitalcommerce360.com/feed/', # Digital Commerce 360
        'https://econsultancy.com/feed/', # Econsultancy - E-commerce and marketing insights
        'https://retaildive.com/rss/feed/', # Retail Dive - e-commerce & retail news
        'https://pymnts.com/feed/', # PYMNTS - e-commerce, payments, fintech
        'https://ecommercetimes.com/perl/syndication/rssfull.pl', # E-Commerce Times
        'https://feeds.feedburner.com/shopify', # Shopify Blog
        'https://www.businessinsider.com/retail/feed', # Business Insider - Retail & e-commerce
        'https://www.internetretailing.net/rss', # Internet Retailing
    ],
    'ai_medicine': [
        'https://www.healthcareitnews.com/home/feed', # Healthcare IT News
        'https://medcitynews.com/feed/', # MedCity News
        'https://aiin.healthcare/feed/', # AI in Healthcare
        'https://feeds.feedburner.com/PharmaPhorum', # PharmaPhorum - Pharma & AI
        'https://www.statnews.com/feed/', # Stat News - Healthcare technology
        'https://www.digitalhealth.net/feed/', # Digital Health - AI and health tech
    ],
    'ai_applications': [
        'https://www.wired.com/feed/', # Wired - Technology section
        'https://venturebeat.com/category/ai/feed/', # VentureBeat - AI applications
        'https://spectrum.ieee.org/rss/robotics', # IEEE Spectrum - Robotics & AI applications
        'https://www.fastcompany.com/technology/rss', # Fast Company - Technology & AI
        'https://feed.sciencedaily.com/mind_brain/artificial_intelligence.xml', # ScienceDaily - AI applications
        'https://www.zdnet.com/topic/artificial-intelligence/rss.xml', # ZDNet - AI applications and industry news
    ],
    'e_payments': [
        'https://pymnts.com/feed/', # PYMNTS - Payments, e-commerce, fintech
        'https://www.finextra.com/rss/finextranews.xml', # Finextra - Financial technology and e-payments
        'https://newsroom.mastercard.com/feed/', # Mastercard Newsroom
        'https://www.visa.com.sg/about-visa/newsroom.html/rss', # Visa Newsroom
        'https://www.paymentssource.com/feed', # PaymentsSource - Payment technology news
        'https://thepaypers.com/rss', # The Paypers - Global payments and fintech news
        'https://www.mobilepaymentstoday.com/rss/', # Mobile Payments Today
    ]
}

class TechnewsService:
    def __init__(self):
        self.key = global_vars.NEWSAPI_API_KEY
        self.logger = LoggerService()


    def fetch_news_for_topic(self, topic, max_items=10) -> list:
        logger_service.info(f"Fetching news for topic: {topic}")
        feeds = rss_feeds.get(topic, [])
        news_items = []
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            logger_service.info(f"Feed: {feed_url}")
            for entry in feed.entries:
                news_items.append({
                    'title': entry.title + '--- body --' + entry.summary,
                })
                logger_service.info(f"News item: {entry.title}")
                if len(news_items) >= max_items:
                    break
            if len(news_items) >= max_items:
                break
        return news_items


    # Function to fetch latest news for all topics
    def fetch_news_for_all_topics(self, topics, max_items_per_topic=10) -> dict:
        all_news = {}
        for topic in topics:
            all_news[topic] = self.fetch_news_for_topic(topic, max_items_per_topic)
        return all_news


    # first_parameter = ['ai', 'e_commerce', 'ai_medicine', 'ai_applications', 'e_payments']
    def get_fresh_headlines(self, first_parameter, second_parameter, connector_id, max_results):
        first_parameter = ['ai_applications']
        first_topic = self.fetch_news_for_all_topics(first_parameter, max_results)
        return first_topic

