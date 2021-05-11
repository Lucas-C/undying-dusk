#!/bin/bash
set -o pipefail -o errexit -o nounset -o xtrace
cd $(dirname ${BASH_SOURCE[0]})

GITHUB_REF=${1?-'git ref must be provided as argument'}
VERSION=${GITHUB_REF##*/}
GAME_ID='undying-dusk'

if [ -z "${BUTLER_API_KEY:-}" ]; then
    echo '$BUTLER_API_KEY undefined - aborting'
    exit 1
fi

echo 'Installing butler CLI:'  # cf. https://itch.io/docs/butler/installing.html
curl -L -o butler.zip https://broth.itch.ovh/butler/linux-amd64/LATEST/archive/default
unzip butler.zip
chmod +x butler
./butler version

cd zip/
ls -lh
echo 'Checking ZIPs:'
../butler auditzip undying-dusk-pdf-only.zip
../butler auditzip undying-dusk-with-sumatra-windows.zip
echo "Now publishing $GAME_ID @ $VERSION ZIPs on itch.io:"
../butler push undying-dusk-pdf-only.zip             Lucas-C/$GAME_ID:pdf-only             --userversion $VERSION
../butler push undying-dusk-with-sumatra-windows.zip Lucas-C/$GAME_ID:with-sumatra-windows --userversion $VERSION
