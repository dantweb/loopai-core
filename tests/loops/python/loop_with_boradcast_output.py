PROMPT_STEP_1_MAX_TOKENS = 50
PROMPT_STEP_2_MAX_TOKENS = 50
PROMPT_STEP_3_MAX_TOKENS = 50
PROMPT_STEP_4_MAX_TOKENS = 50

PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "Generate answer on the topic in the field 'requestContent' taking into account all other fields in "
                   "this json. Your response should be a valid json as in the field 'response'",
        "language": "english",
        "requestContent": "{{REQUEST_CONTENT}}",
        "region": "USA",
        "format": "json",
        "response": {
            "title": "text",
            "summary": "149 chars long text",
            "lead_paragraph": "not longer than 300 symbols",
            "subtutle1": "subtitle for part 1",
            "subtutle2": "subtitle for part 2",
            "subtutle3": "subtitle for part 3",
            "paragraph1": "700-800 symbols text for part 1",
            "paragraph2": "700-800 symbols text for part 2",
            "paragraph3": "700-800 symbols text for part 3",
        }
    },

    #prompt for second step
    "PROMPT_STEP_2_JSON": "Generate vibrant high resolution image imitating oil "
                          "painting and modern arts for this description: {{DESCRIPTION}}"
}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "You are chef editor at a blog which focuses on topics such as healthcare and beauty"
    },
    "SYSTEM_CONTENT_STEP_2": {
        "role": "system",
        "content": "You are an image editor and an artist who works as an art director"
                   "at a famous blog about health and beauty"
    }
}
