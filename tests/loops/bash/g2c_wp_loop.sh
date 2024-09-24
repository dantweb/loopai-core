#!/bin/bash

rm -rf /home/dtkachev/jesus/wordpress/wp-content/plugins/loopai-woo-consultant
cp -rf /home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/loopai-wp-cons /home/dtkachev/jesus/wordpress/wp-content/plugins/loopai-woo-consultant

echo "Deployed\n"
