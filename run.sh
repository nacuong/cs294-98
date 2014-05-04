#!/bin/bash

#python python-to-racket.py -t tests/hw2-1-t.py -s tests/hw2-1-s.py -m product -u 10 -b "(5,15),(7,38)" -c parallel

strategies=( #parallel 
mixer priority mixer-priority
)
programs=(
"-t tests/hw2-1-t.py -s tests/hw2-1-s.py -m product -u 10 -b (5,15),(7,38)"
"-t tests/hw1-4-t.py -s tests/hw1-4-s.py -m hailstone -u 10 -l 0 -b (3,15)"
"-t tests/computeDeriv-t2.py -s tests/computeDeriv-s1.py -m computeDeriv -a 0 -b (4,20),(9,14)"
"-t tests/everyOther-t1.py -s tests/everyOther-s1.py -m everyOther -l -5 -u 5 -a 0 -b (3,13)"
"-t tests/everyOther-t1.py -s tests/everyOther-s2.py -m everyOther -l -5 -u 5 -a 0 -b (4,21),(5,14),(6,20)"
"-t tests/multIA-t.py -s tests/multIA-s1.py -m multIA -u 10 -l 0 -b (3,13),(5,8)"
"-t tests/evaluatePoly-t4.py -s tests/evaluatePoly-s2.py -m evaluatePoly -u 5 -l -5 -a 0 -b (6,19)"
"-t tests/evaluatePoly-t4.py -s tests/evaluatePoly-s4.py -m evaluatePoly -u 5 -l -5 -a 0 -b (6,23)"
"-t tests/evaluatePoly-t4.py -s tests/evaluatePoly-s3.py -m evaluatePoly -l -5 -u 5 -a 0 -b (11,24)"
)

for program in "${programs[@]}"
do
    for strategy in "${strategies[@]}"
    do
        echo python python-to-racket.py $program -c $strategy
        python python-to-racket.py $program -c $strategy 2> error
    done
    echo python python-to-racket.py $program -c parallel
    sleep 10
    python python-to-racket.py $program -c parallel 2> error
    sleep 60
done