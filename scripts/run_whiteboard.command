#!/bin/bash
cd `dirname $0`
cd ..

make whiteboard

open data/figs/projects/projects.html
open data/figs/people/people.html
