#!/bin/bash
set -o pipefail -o errexit -o nounset -o xtrace
cd $(dirname ${BASH_SOURCE[0]})

VERSION=${1?-'Version must be provided as argument'}
GAME_ID='undying-dusk'

if [ -z "${BUTLER_API_KEY:-}" ]; then
    echo '$BUTLER_API_KEY undefined - aborting'
    exit 1
fi

echo 'Installing butler CLI:'  # cf. https://itch.io/docs/butler/installing.html
curl -L -o butler.zip https://broth.itch.ovh/butler/linux-amd64/LATEST/archive/default
unzip butler.zip
chmod +x butler
./butler -V

# Publish a folder that IS *exactly* the release build:
mkdir -p itchio && rm -f itchio/*.*
cp -t itchio/ zip/undying-dusk-pdf-only.zip zip/undying-dusk-with-sumatra-windows.zip
echo "Now publishing $GAME_ID @ $VERSION on itch.io:"
./butler push itchio Lucas-C/$GAME_ID:pdf --userversion $VERSION
