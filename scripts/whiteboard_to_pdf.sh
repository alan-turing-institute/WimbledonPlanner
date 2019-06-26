#!/bin/bash
cd $(cd -P -- "$(dirname -- "$0")" && pwd -P)

pwd
ls

if [[ "$?" != "0" ]]; then
    echo "[Error] cd ../data/figs/projects failed!"
    exit 10
fi

cd ../data/figs/projects
pwd
ls

if [[ "$?" != "0" ]]; then
    echo "[Error] cd ../data/figs/projects failed!"
    exit 11
fi

wkhtmltopdf -T 0 -B 0 --page-width 2000mm --page-height 2000mm projects.html tmp.pdf
if [[ "$?" != "0" ]]; then
    echo "[Error] wkhtmltopdf -T 0 -B 0 --page-width 2000mm --page-height 2000mm projects.html tmp.pdfs failed!"
    exit 12
fi

pdf-crop-margins -p 0 -a -10 tmp.pdf -o projects.pdf
if [[ "$?" != "0" ]]; then
    echo "[Error] pdf-crop-margins -p 0 -a -10 tmp.pdf -o projects.pdf failed!"
    exit 13
fi

rm tmp.pdf
if [[ "$?" != "0" ]]; then
    echo "[Error] rm tmp.pdf failed!"
    exit 14
fi

cd ../people
pwd
ls

if [[ "$?" != "0" ]]; then
    echo "[Error] cd ../people failed!"
    exit 15
fi

wkhtmltopdf -T 0 -B 0 --page-width 2000mm --page-height 2000mm people.html tmp.pdf
if [[ "$?" != "0" ]]; then
    echo "[Error] wkhtmltopdf -T 0 -B 0 --page-width 2000mm --page-height 2000mm people.html tmp.pdf failed!"
    exit 16
fi

pdf-crop-margins -p 0 -a -10 tmp.pdf -o people.pdf
if [[ "$?" != "0" ]]; then
    echo "[Error] pdf-crop-margins -p 0 -a -10 tmp.pdf -o people.pdf failed!"
    exit 17
fi

rm tmp.pdf
if [[ "$?" != "0" ]]; then
    echo "[Error] rm tmp.pdf failed!"
    exit 18
fi
