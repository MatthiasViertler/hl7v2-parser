#!/bin/bash
for i in {1..5}; do
  printf "\x0b$(cat sample_oru_glucose.hl7)\x1c\x0d"
done | nc localhost 2575

