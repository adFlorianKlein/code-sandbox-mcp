#!/usr/bin/env bash
set -e

VERSION="${1:-$(cat VERSION 2>/dev/null || echo "latest")}"

# base is always built — only these are selectable
declare -a IMAGES=(
    "nodejs:docker/nodejs.Dockerfile:code-sandbox-nodejs"
    "java:docker/java.Dockerfile:code-sandbox-java"
    "full:docker/full.Dockerfile:code-sandbox-full"
)

# Toggle state: 1=selected, 0=not selected (all on by default)
declare -a SELECTED=(1 1 1)

print_menu() {
    clear
    echo "=== code-sandbox build menu (tag: $VERSION) ==="
    echo ""
    echo "  [*] base  (wird immer gebaut)"
    echo ""
    for i in "${!IMAGES[@]}"; do
        name="${IMAGES[$i]%%:*}"
        if [[ "${SELECTED[$i]}" -eq 1 ]]; then
            marker="[x]"
        else
            marker="[ ]"
        fi
        if [[ "$i" -eq "$CURSOR" ]]; then
            echo " > $marker $name"
        else
            echo "   $marker $name"
        fi
    done
    echo ""
    echo "← → = navigieren | Leertaste = auswählen | Enter = bauen | q = abbrechen"
}

CURSOR=0

while true; do
    print_menu
    # Erster Read blockiert bis eine Taste gedrückt wird
    IFS= read -rsn1 key

    # ESC-Sequenz (Pfeiltasten): zweiten Teil mit kurzem Timeout nachlesen
    if [[ "$key" == $'\e' ]]; then
        IFS= read -rsn2 -t 0.1 rest || rest=""
        key="$key$rest"
    fi

    case "$key" in
        $'\e[D'|$'\eOD')   # Pfeil links
            CURSOR=$(( (CURSOR - 1 + ${#IMAGES[@]}) % ${#IMAGES[@]} ))
            ;;
        $'\e[C'|$'\eOC')   # Pfeil rechts
            CURSOR=$(( (CURSOR + 1) % ${#IMAGES[@]} ))
            ;;
        ' ')               # Leertaste
            SELECTED[$CURSOR]=$(( 1 - SELECTED[$CURSOR] ))
            ;;
        ''|$'\n'|$'\r')    # Enter
            break
            ;;
        q|Q)
            echo "Abgebrochen."
            exit 0
            ;;
    esac
done

echo ""
echo "Baue mit tag: $VERSION"
echo ""

BUILT=()

# base immer zuerst
echo "--- base ---"
docker build -f docker/base.Dockerfile -t "code-sandbox-base:$VERSION" .
BUILT+=("code-sandbox-base:$VERSION")

# selektierte images
for i in "${!IMAGES[@]}"; do
    [[ "${SELECTED[$i]}" -eq 0 ]] && continue
    entry="${IMAGES[$i]}"
    name="${entry%%:*}"
    rest="${entry#*:}"
    dockerfile="${rest%%:*}"
    tag="${rest#*:}"

    echo ""
    echo "--- $name ---"
    docker build -f "$dockerfile" -t "$tag:$VERSION" --build-arg BASE_VERSION="$VERSION" .
    BUILT+=("$tag:$VERSION")
done

echo ""
echo "Fertig. Gebaut: ${BUILT[*]}"
