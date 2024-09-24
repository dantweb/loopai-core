


ARTICLE_EXAMPLE = ""

PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "In the field 'requestContent' there are input data. Your response should be only and strictly a json with the structure of the field 'resonse'",
        "language": "english",
        "requestContent": "{{REQUEST_CONTENT}}",
        "format": "json",
        "response": {
            [
                {
                    'path': '/some/path/to/the/file',
                    'file_content': 'file_content'
                }
            ]
        }
    }
}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "You develop a module in PHP8.2 declare strict types with PSR-12, clean code, SOLID, TDD"
    },

}

# def if_function_example(arg1: int, arg2: int): bool
#     if arg1 > arg2:
#         return True
#     else:
#         pass
