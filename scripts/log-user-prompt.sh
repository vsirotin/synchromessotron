#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract the prompt text using jq
prompt=$(echo "$input" | jq -r '.prompt // empty')

# If prompt is not empty, append it to TMP/user-commands.txt
if [ -n "$prompt" ]; then
  echo "$prompt" >> TMP/user-commands.txt
fi
