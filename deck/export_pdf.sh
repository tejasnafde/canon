#!/bin/sh
# Export deck/canon-deck.pptx to deck/canon-deck.pdf with Keynote (LibreOffice is not installed here).
set -e
cd "$(dirname "$0")"
osascript <<OSA
tell application "Keynote"
  set d to open POSIX file "$PWD/canon-deck.pptx"
  export d to POSIX file "$PWD/canon-deck.pdf" as PDF
  close d saving no
  quit
end tell
OSA
ls -l canon-deck.pdf
