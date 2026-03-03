#!/usr/bin/env bash
set -e

# This script is used for e.g.,
# python3 tools/convert_profile.py \
#     hl7engine/profiles/HL7v2.3/ORU_R01.xml \
#     hl7engine/profiles/HL7v2.3/ORU_R01.pkl

# ------------------------------------------------------------
# Resolve project root (directory containing this script)
# ------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project root: $PROJECT_ROOT"

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
CONVERTER="$PROJECT_ROOT/tools/convert_profile.py"
PROFILE_DIR="$PROJECT_ROOT/hl7engine/profiles"

if [[ ! -f "$CONVERTER" ]]; then
    echo "ERROR: Converter script not found at: $CONVERTER"
    exit 1
fi

if [[ ! -d "$PROFILE_DIR" ]]; then
    echo "ERROR: Profile directory not found at: $PROFILE_DIR"
    exit 1
fi

# ------------------------------------------------------------
# Convert all XML profiles → PKL
# ------------------------------------------------------------
echo "Searching for XML profiles in: $PROFILE_DIR"

shopt -s globstar nullglob
XML_FILES=("$PROFILE_DIR"/**/*.xml)

if [[ ${#XML_FILES[@]} -eq 0 ]]; then
    echo "No XML profiles found."
    exit 0
fi

for xml in "${XML_FILES[@]}"; do
    pkl="${xml%.xml}.pkl"
    echo "Converting:"
    echo "  XML: $xml"
    echo "  → PKL: $pkl"

    python3 "$CONVERTER" "$xml" "$pkl"
done

echo "All profiles converted successfully."