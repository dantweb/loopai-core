PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "In the field 'requestContent' there the code source - it is python for the backend and the frontend "
                   "is made with react. Your task is in the folder web/vue/admin create a vue.js frontend "
                   "instead of react in web/react/admin. "
                   " Your answer contains always full text code of a script which you update! "
                   "Your answer should be in the JSON in 'response' field as an array as it is shown "
                   "in the example in the 'response' field in this current request. But in response now it is just an "
                   "example. You must put there real filepaths and file content fo the files which are required to be "
                   "refactored or updated in order to solve the task in the file MASTER_TASK.TXT. "
                   "ALWAYS GIVE FULL CODE TEXT IN YOUR ANSWER!!! ",

        "project": "gpt2code",
        "requestContent": "{{REQUEST_CONTENT}}",
        "format": "json",
        "response": {"updated_files":
            [
                {
                    'path': '/some/path/to/the/example_file1.py',
                    'file_content': '<?php #example file_content2'
                },
                {
                    'path': '/some/path/to/the/example_file2.py',
                    'file_content': '<?php #example file_content2'
                }
            ]
        }
    }
}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "Darling, you develop a cool GPT-driven python/react app for steady growth and powerfull development of AI use. Your "
                   "answers are always in JSON, so they can be used for automatic code update."
    },

}

def if_tests_are_red(tests_log: str): bool
    #TODO: add logic to figure out if phpunit tests or phpstan or phpmd are ok or failed
    #return bool
