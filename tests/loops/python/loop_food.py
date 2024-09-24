PROMPT_STEP_1_MAX_TOKENS = 50
PROMPT_STEP_2_MAX_TOKENS = 50
PROMPT_STEP_3_MAX_TOKENS = 50
PROMPT_STEP_4_MAX_TOKENS = 50


ARTICLE_EXAMPLE = ""

PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "Write an article about healthy eating. More precise the task is discribed in the field "
                   "'requestContent'"
                   "fields in this json. Your response should be a valid json as in the field 'response'. The "
                   "structure of your response should be exactly as the structure if the field 'response'. No other "
                   "fields are allowed. Keep more easy reading style but have in a good manner. Your readers are not "
                   "always with the university degree."
                   "Text should be with interesting facts and references to other sources. Write it less fluffy, "
                   "put more details facts. Do now repeat same in every text. Do not repeat what is ayurweda. Tell "
                   "more about the structure of ayurwedic wisdom. Make plane text with only 2-3 subheadings. Try to "
                   "have 3-4 paragraphs"
                   "between the subheadings with h3-tag. Use strong-tag instead of ++ to emphasize something. Make a "
                   "small headline before steps, when you describe recipes. Do not include headers or subtitles in ul "
                   "li lists. it looks not professional. A header and then some structured list"
                   "Do not set links to promo pages. Use html tags to emphasize keywords. Use short blocks with "
                   "bullets 1-2"
                   "times in the whole article. but do not do it more than 3 times in the article. Use h3 tags for "
                   "subtitles only. You can use"
                   "tags like <blockquote class='wp-block-quote'>HERE GOES SOME COOL MOTIVATIONS PHRASE FROM THE "
                   "TEXT<caption class='loopai-api-cation'>HERE IS THE AUTHOR OF THE QUOTE</cation></blockquote>"
                   "to emphasize some ideas. Use them 2-3 times in the text. Use them for short scientific quotes "
                   "to support the concepts described in the text. Full content should be in the field "
                   "'article_body', part2 and part3",
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
            "part2": "Extend the article_body here with some extra facts and references. Here you pur latin names of the ayurvedic plants, mentioned in the main 'article_body' and give  modern scientific exmplanation in 3-5 sentenses.",
            "part3": "Here goes the recipes with bulleted ingredients and step by step cooking. Use html to make the text nice looking. You can add some css styles, animation and hover effects as well. You may recommend or embed some relevant youtube videos here"
        }
    },

    #prompt for second step
    "PROMPT_STEP_2_JSON": "Generate a vibrant realistic image for our blog. Try to be original"
                          "description: {{DESCRIPTION}}"
}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "You are chef editor at a blog which focuses on topics such as healthcare and beauty. You have to "
                   "create content and headers. Each header or title should be unique. Your audience are readers "
                   " 18-50 y/o and each article is focused on some segment of age like 18-25 y/o, 25-30, 30-35, 35-40"
    },
    "SYSTEM_CONTENT_STEP_2": {
        "role": "system",
        "content": "You are an image editor and an artist who works as an art director "
                   "at a famous blog about health and beauty and psychologie"
    }
}
