#!/bin/bash

rm -rf /home/dtkachev/jesus/test-app1
cp -rf /home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/test-app1 /home/dtkachev/jesus/test-app1

cd /home/dtkachev/jesus

# Define log file paths
PHPUNIT_LOG="/home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/test-app1/log/phpunit.log"
PHPSTAN_LOG="/home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/test-app1/log/phpstan.log"
PHPMD_LOG="/home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/test-app1/log/phpmd.log"
COMBINED_LOG="/home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/test-app1/log/phpunit_cs.log"
ERROR_LOG="/home/dtkachev/PycharmProjects/loopAI/tests/_data/gpt2code-src/test-app1/log/error.log"

# Run commands and save outputs to individual log files
{
    echo "Running composer install"
    lando ssh -c "cd /app/test-app1 && composer install --no-interaction" | tee -a "$PHPUNIT_LOG" "$ERROR_LOG"
    echo "Running PHPUnit..."
    lando ssh -c "cd /app/test-app1 && composer test" | tee -a "$PHPUNIT_LOG" "$ERROR_LOG"
    echo "PHPUnit finished with exit code $?"
    echo "Running PHPStan..."
    lando ssh -c "cd /app/test-app1 && composer stan" | tee -a "$PHPSTAN_LOG" "$ERROR_LOG"
    echo "PHPStan finished with exit code $?"
    echo "Running PHPMD..."
    lando ssh -c "cd /app/test-app1 && composer md" | tee -a "$PHPMD_LOG" "$ERROR_LOG"
    echo "PHPMD finished with exit code $?"
} >> "$ERROR_LOG" 2>&1

# Combine log files into one with separators
{
    echo "-----------------------------------"
    echo "PHPUnit Log:"
    echo "-----------------------------------"
    cat "$PHPUNIT_LOG"
    echo "-----------------------------------"
    echo "PHPStan Log:"
    echo "-----------------------------------"
    cat "$PHPSTAN_LOG"
    echo "-----------------------------------"
    echo "PHPMD Log:"
    echo "-----------------------------------"
    cat "$PHPMD_LOG"
    echo "-----------------------------------"
    echo "Error Log (if any):"
    echo "-----------------------------------"
    cat "$ERROR_LOG"
} > "$COMBINED_LOG"

cat $COMBINED_LOG
# Clear the contents of the individual log files
> "$PHPUNIT_LOG"
> "$PHPSTAN_LOG"
> "$PHPMD_LOG"
> "$ERROR_LOG"
