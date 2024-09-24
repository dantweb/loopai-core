PROMPT_STEP_1_MAX_TOKENS = 50
PROMPT_STEP_2_MAX_TOKENS = 50
PROMPT_STEP_3_MAX_TOKENS = 50
PROMPT_STEP_4_MAX_TOKENS = 50

PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "Generate an article for a blog about botanics and medical use of plants and also for healthcare "
                   "based on the text in the field 'requestContent' taking into account all other"
                   "fields in this json. Your response should be a valid json as in the field 'response'. The "
                   "structure of your response should be exactly as the structure if the field 'response'. No other "
                   "fields are allowed."
                   "subtitle1, subtitle2, subtitle3 are very important fields. Paragraph4 must be a story with "
                   "interesting facts and references to other sources. This part contains of 30 sentences and split "
                   "into smaller paragraphs. Minimum length of the 'paragraph4' is 2000 symbols. If you say 'modern "
                   "research' add link to the source. Write it less fluffy, more details. Style for this paragraph is "
                   "easy reading about history of science.",
        "language": "english",
        "requestContent": "{{REQUEST_CONTENT}}",
        "region": "USA",
        "format": "json",
        "response": {
            "title": "text",
            "summary": "250 chars long text",
            "seo_description": "129 chars long text",
            "seo_keyword": "short search keyword",
            "tags": "30 coma-separated tags including deseases or symptoms which cures or causes",
            "category": "Poisonous plants",
            "lead_paragraph": "not longer than 300 symbols",
            "subtitle1": "subtitle for part 1 - medical use",
            "subtitle2": "subtitle for part 2 - usefull chemicals or molecules",
            "subtitle3": "subtitle for part 3 - how to prepare for medical use",
            "subtitle4": "subtitle for part 4 - how it was discovered",
            "paragraph1": "500 words text for part 1 - where it grows, which parts are important for medical use and "
                          "in which season. Use html tags to emphasize the text, not more then once in a paragraph.",
            "paragraph2": "500 words text for part 2 - medical use, usefull chemicals or molecules, how to extract "
                          "them, give a few examples of industrial usage of these molecuúles",
            "paragraph3": "500 words text for part 3 - how to prepare for medical use or how to extract poisonous "
                          "substances and alcaloids. Give exact sructured recipe. Use html tags "
                          "like ul and li to show proper list of ingredients under separate local subheading but in "
                          "the text just with html tags h3. Use html tags to emphasize the text, not more then once "
                          "in a paragraph",
            "paragraph4": "here write a story about how the healing properties or compounds were discovered and how "
                          "they were used in historical times. Maybe some facts from medieval times or XIX century",
        }
    },

    #prompt for second step
    "PROMPT_STEP_2_JSON": "Generate a vibrant realistic image imitating real plant in nature for this "
                          "description: {{DESCRIPTION}}"
}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "You are chef editor at a blog which focuses on topics such as healthcare and beauty. You have to "
                   "create content and headers. Each header or title should be unique. Do no use always same words "
                   "like 'Harnessing Power' or 'the healing power'. USe html tags to emphasize with bold hot key "
                   "words  and botanical names but only in paragraphs and subtitles and not in header or titles. Do "
                   "not text emphasizing it too often. Not every time. Please not every time use 'Exploring the Dual "
                   "Nature'. Imagine you have 40 different cliché which you can use. This title is an example of a "
                   "googd title 'Sweet Marjoram: The Gentle Healer' and this title is also good 'The Many Virtues of "
                   "Mullein: A Closer Look at Verbascum thapsus'",
    },
    "SYSTEM_CONTENT_STEP_2": {
        "role": "system",
        "content": "You are an image editor and an artist who works as an art director"
                   "at a famous blog about health and beauty. Some of your pictures should be like from botanics "
                   "books some pictures should be like realistiic plant in nature. When you think it is cool, "
                   "add chemical structured formulas"
    }
}
