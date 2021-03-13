#!/bin/bash

set -o pipefail -o errexit -o nounset

cd $( dirname "${BASH_SOURCE[0]}" )

zip undying-dusk-pdf-only.zip ../undying-dusk.pdf

wget https://www.sumatrapdfreader.org/dl/SumatraPDF-3.1.2.zip
unzip SumatraPDF-3.1.2.zip

zip undying-dusk-with-sumatra-windows.zip LAUNCH_UNDYING_DUSK_IN_SUMATRA.bat HOW_TO_PLAY.txt SumatraPDF.exe ../undying-dusk.pdf
