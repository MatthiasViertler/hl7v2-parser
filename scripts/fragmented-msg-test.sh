#!/bin/bash

printf "\x0bMSH|^~\\&|LAB|HOSP|" | nc localhost 2575
sleep 1
printf "EHR|HOSP|202402201200||ORU^R01|" | nc localhost 2575
sleep 1
printf "12345|P|2.5.1\rPID|1||123456^^^HOSP^MR||Doe^John||19800101|M\r" | nc localhost 2575
sleep 1
printf "OBR|1||987654|GLUCOSE^Glucose Test^L\rOBX|1|NM|2345-7^Glucose^LOINC||5.6|mmol/L|3.9-5.5|H\x1c\x0d" | nc localhost 2575

