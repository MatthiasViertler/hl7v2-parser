#!/bin/bash
{
  printf "\x0b$(cat sample_adt_a01.hl7)\x1c\x0d"
  printf "\x0b$(cat sample_orm_o01.hl7)\x1c\x0d"
  printf "\x0b$(cat sample_oru_hb.hl7)\x1c\x0d"
} | nc localhost 2575


