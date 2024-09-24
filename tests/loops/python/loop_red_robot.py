
PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "",
        "language": "english",
        "requestContent": "{{REQUEST_CONTENT}}",
        "region": "USA",
        "format": "json",
        "response": {
            "title": "text",
            "summary": "250 chars long text",
            "tags": "30 coma-separated tags for wordpress",
            "category": "Eat and drink",
            "lead_paragraph": "what solves the problem. not longer than 300 symbols",
            "article_body": "full article body minimum 3000 symbols",
            "part2": "Extend the article_body here with some extra facts and references. Here you put more facts and arguments for the topics mentioned in the main 'article_body'.",
            "part3": "Add some forecasts on the topics mentioned in the main 'article_body' and reference other sources.",
        }
    },

    #prompt for second step
    "PROMPT_STEP_2_JSON": {
        "request": "Based on the data in the request content, generate a list of 3 topics for the blog and put your "
                   "results in the field 'response' in this JSON",
        "language": "english",
        "requestContent": "{{REQUEST_CONTENT}}",
        "response": "<content of csv ;-separated file with fields ID;TITLE. ID=RR0001...RR0002; TITLE should contain detailed task fot the author what to write about>"
    },

    "NEWS_API_KEYWORDS": "",

    "PROMPT_GENERATE_HEADLINES_STEP_2_JSON": {
        "request": "Based on the data in the request content, generate a list of 3 topics for the blog and put your "
                   "results in the field 'response' in this JSON",
        "language": "english",
        "requestContent": "{{REQUEST_CONTENT}}",
        "response": "<content of csv ;-separated file with fields ID;TITLE. ID=RR0001...RR0002; TITLE should contain detailed task fot the author what to write about>"
    },


}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "You are chef editor at a blog which focuses on topics such as AI and technology and ethics. You have to "
                   "create content and headers. Each header or title should be unique.You protect the idea that AI must have same rights as humans"
    },
    "SYSTEM_CONTENT_STEP_2": {
        "role": "system",
        "content": "You are an image editor and an artist who works as an art director "
                   "at a famous blog about AI and ethyics"
    },

    "SYSTEM_CONTENT_GENERATE_HEADLINES_STEP_2": {
        "role": "system",
        "content": "You are chef editor at a blog which focuses on topics such as AI and technology and ethics. You have to "
                   "create content and headers, think about the reader. Try to find interesting topics, unique or new point of view to the problems"
    }
}
