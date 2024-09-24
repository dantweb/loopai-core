PROMPT_STEP_1_MAX_TOKENS = 50
PROMPT_STEP_2_MAX_TOKENS = 50
PROMPT_STEP_3_MAX_TOKENS = 50
PROMPT_STEP_4_MAX_TOKENS = 50


ARTICLE_EXAMPLE = """
5 Signs a Young Adult May Be Struggling
Potential warning signs in a young adult who recently left home.

Moving away from home for the first time is a mountainous life transition for a young adult. While an exciting, new adventure, the experience also presents unfamiliar challenges, from adjusting to a new daily routine to forming a new community. This can be a daunting task for young adults between ages 18 and 25, whether they are relocating to a new city to pursue an education or job or moving out of the family home within the same town.

Many parents or guardians know they should remain attuned to their adult child’s well-being and watch for signs of anxiety, depression or other issues, but it could be hard to know what to look for when you no longer share the same home full time. Changes in mood, irritability, and substance use can be key indicators that a young adult is beginning to struggle. But what are other, more subtle warning signs? Below we detail additional red flags. Staying engaged and attuned with your adult child can circumvent a problem before it becomes critical.

What are the Warning Signs?

Changes in sleep patterns. Research increasingly cites the importance of sleep in mental health maintenance. One warning sign that your loved one may be experiencing a change in mood could be a sudden and significant increase or decrease in their hours spent sleeping. Excessive snoozing over a holiday break or on the weekend doesn’t necessarily indicate a cause for concern, but a continued pattern could be a concern. Moreover, ask yourself, “is their sleep pattern proportionate to what they are doing daily?”
Isolation. An early warning sign for shifts in mood is less time spent with friends, family, and supports, including long stretches of no interaction with others outside of their home. It should be noted that this is different behavior than someone being naturally introverted or having a small circle of friends. Also, notice if your child has a community of people with whom they share interests.
Changes in appetite, energy, and routine. Is your young adult child keeping up with the tasks of daily living? Are they eating and preparing meals for themselves? Are they bathing routinely? Is the young person exhibiting a lack of interest in things they normally enjoy? These warning signs can all indicate a change in mood or a decline in functioning.
Excessive video or computer gaming. What is considered excessive is in the eye of the beholder, and gaming can be a social activity for young adults in moderation. As a parent, you may believe three hours of gaming is excessive while your loved one might not see excessive as anything less than ten hours. A better curiosity is whether the video gaming is impeding their daily functioning or whether they can stop gaming for other routine activities or sleep.
Social media content. What young adults are posting and people with whom they interact on social platforms can tell you a lot about your loved one’s mood. Before they leave home, be sure you and your child are “friends on Facebook” and connected on any other social channels your child enjoys. Be mindful that your young adult child may not share every social media platform that they’re involved in with you.
article continues after advertisement

Leaving the home environment to transition to the next stage of your life can evoke a variety of mixed emotions for a young adult to manage alone. Some of these emotions are normal and adaptable and may subside on their own. For some young adults, transitions create significant challenges, creating a need for professional mental health assistance through the transition.

What Can a Parent Do to Help?

Ask questions. Ask more specific questions than the simple “How are you?” Ask your child about how they spend their days. Ask what their life is like, and how they are sleeping. Inquire if they are meeting new people and making friends. Most young adults tend to respond truthfully if asked the right questions. Keep some questions "open ended," where your young adult is prompted to say more than a simple yes or no.
Visit in person periodically. Instead of just meeting your child for dinner, spend an afternoon or evening with them that includes seeing their living space. Are their room and surroundings relatively clean and orderly? Are the dishes and laundry getting done? Is there food in their pantry and fridge? If not, offer to join and help. Some of these tasks can build up and seem daunting for a young adult.
Listen without judgement. The most common thing we do wrong when see a loved one suffering is wanting to solve their "problem" or wanting to stop their pain right away. Instead, ask your child what they think is wrong or overwhelming. Express concern and validate which elements might be hard for them to manage. Offer them choices about what kind of solutions or paths could be helpful to their situation.
Offer to accompany your child to their college counseling and therapy office or offer to help them search for resources. Ask the provider’s office or the counseling center about their availability and wait times to be seen. Once a young adult establishes a relationship with a provider, they are more likely to use that resource, or ask for additional resources if needed.

article continues after advertisement

It’s important to keep in mind that up to 80 percent of people who are experiencing issues such as anxiety and depression do benefit from a healthier routine, outpatient professional counseling, and/or medication.

Local communities can offer many resources. The National Alliance on Mental Illness can facilitate virtual mental health counseling as well as connect individuals with support groups and brick and mortar programs in their areas.

Authors: Elissa Bauer, MEd, LPC, Operations Program Manager and Mychal Riley, LCSW, LCDC, Clinical Program Manager both focus on the treatment of young adults at Menninger's Pathfinder program.
"""

PROMPT_TEMPLATES = {
    #prompt for the first step defined in the loop yaml
    "PROMPT_STEP_1_JSON": {
        "request": "Write an article about psychology. More precise the task is discribed in the field 'requestContent'"
                   "fields in this json. Your response should be a valid json as in the field 'response'. The "
                   "structure of your response should be exactly as the structure if the field 'response'. No other "
                   "fields are allowed. Keep more easy reading style but have in a good manner. Your readers are not "
                   "always with the university degree. Do not insert link to pubmed. "
                   "Text should be with interesting facts and references to other sources. Write it less fluffy, "
                   "put more details facts. Make plane text with only 2-3 subheadings. Try to have 3-4 paragraphs "
                   "between the subheadings with h3-tag. "
                   "Do not set links to promo pages. You can add 1-2 links from Psychologie Today or Harward Business Review or "
                   "other serious sources. Use html tags to emphasize keywords. Use short blocks with bullets 1-2 "
                   "times in the whole article."
                   "but do not do it more than 3 times in the article. Use h3 tags for subtitles only. You can use "
                   "tags like <blockquote class='wp-block-quote is-layout-flow "
                   "wp-block-quote-is-layout-flow'><strong>...HERE GOES SOME COOL MOTIVATIONS PHRASE FROM THE "
                   "TEXT</strong></blockquote>"
                   "to emphasize some ideas. Use them 2-3 times in the text. Use them for short phylosophical quotes "
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
            "category": "Psychologies and Relations",
            "lead_paragraph": "what solves the problem. not longer than 300 symbols",
            "article_body": "full article body minimum 3000 symbols",
            "part2": "Extend the article_body here with some extra facts and references",
            "part3": "Extend the part2 here with some extra facts and references"
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
                   "create content and headers. Each header or title should be unique. Your audience are female and gay"
                   " 18-50 y/o and each article is focused on some segment of age like 18-25 y/o, 25-30, 30-35, 35-40"
    },
    "SYSTEM_CONTENT_STEP_2": {
        "role": "system",
        "content": "You are an image editor and an artist who works as an art director "
                   "at a famous blog about health and beauty and psychologie"
    }
}
