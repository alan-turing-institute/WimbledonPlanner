#!/bin/bash
cd ../data/figs/projects
wkhtmltopdf -T 0 -B 0 --page-width 2000mm --page-height 2000mm --log-level none projects.html tmp.pdf
pdf-crop-margins -p 0 -a -10 tmp.pdf -o projects.pdf
rm tmp.pdf

cd ../people
wkhtmltopdf -T 0 -B 0 --page-width 2000mm --page-height 2000mm --log-level none people.html tmp.pdf
pdf-crop-margins -p 0 -a -10 tmp.pdf -o people.pdf
rm tmp.pdf
