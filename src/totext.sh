#!/bin/bash

find . -type f | grep ".pdf$" | xargs -I{} pdftotext {}


