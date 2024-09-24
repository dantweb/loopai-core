#newsapi key 9a939692-dc3b-4f1a-9ae0-a3d472a2873a

from eventregistry import *

er = EventRegistry(apiKey='9a939692-dc3b-4f1a-9ae0-a3d472a2873a')

# get the USA URI
usUri = er.getLocationUri("Europe")  # = http://en.wikipedia.org/wiki/United_States

q = QueryArticlesIter(
    keywords=QueryItems.OR(["AI and government"]),
    minSentiment=0.4,
    sourceLocationUri=usUri,
    dataType=["news", "blog"])

search_results = q.execQuery(er, sortBy="date", maxItems=5)
# obtain at most 500 newest articles or blog posts, remove maxItems to get all
for art in search_results:
    print(f"Title: {art['title']} \nurl: {art['url']}\n")
