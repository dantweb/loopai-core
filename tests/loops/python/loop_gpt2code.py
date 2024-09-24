PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "In the field 'requestContent' there are test logs and code style checkup reports and the source "
                   "code. Your task is to decode the input, "
                   "understand it, think, update or refactor or"
                   "create new code in most effective way. You will do this in many "
                   "iterations. Your answer should be in the JSON in 'response' field as an array as it is shown "
                   "in the example in the 'response' field in this current request. But in response now it is just an "
                   "example. You must put there real filepaths and file content fo the files which are required to be "
                   "refactored or updated in order to solve the issues by phpstan, phpunit, phpmd and other possible "
                   "errors ",
        "project": "gpt2code",
        "requestContent": "{{REQUEST_CONTENT}}",
        "format": "json",
        "response": {"updated_files":
            [
                {
                    'path': '/some/path/to/the/example_file1.php',
                    'file_content': '<?php #example file_content2'
                },
                {
                    'path': '/some/path/to/the/example_file2.php',
                    'file_content': '<?php #example file_content2'
                }
            ]
        }
    }
}

SYSTEM_CONTENT_TEMPLATES = {
    "SYSTEM_CONTENT_STEP_1": {
        "role": "system",
        "content": "Darling, you develop a module in PHP8.2 declare strict types with PSR-12, clean code, SOLID, TDD. Your "
                   "answers are always in JSON, so they can be used for automatic code update."
    },

}

def if_tests_are_red(tests_log: str): bool
    #TODO: add logic to figure out if phpunit tests or phpstan or phpmd are ok or failed
    #return bool
