#!/bin/bash
cd `dirname $0`

make whiteboard

open ../data/figs/projects/projects.html
open ../data/figs/people/people.html
