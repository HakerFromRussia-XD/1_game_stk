#!/bin/sh
# Build-owned thumbnails keep uninstalled campaign cards visible without
# embedding their complete maps.  The output is transient bundle data.
set -eu

source_root=${1:?missing source tracks root}
campaign=${2:?missing campaign manifest}
destination_root=${3:?missing destination preview root}

rm -rf "$destination_root"
mkdir -p "$destination_root"

/usr/bin/ruby -rrexml/document -e '
  tracks_root, manifest = ARGV
  campaign = REXML::Document.new(File.read(manifest))
  campaign.elements.each("campaign/event") do |event|
    id = event.attributes.fetch("track").to_s
    track = REXML::Document.new(File.read(File.join(tracks_root, id, "track.xml")))
    screenshot = track.root.attributes.fetch("screenshot").to_s
    puts [id, File.join(tracks_root, id, screenshot)].join("\t")
  end
' "$source_root" "$campaign" | while IFS="$(printf '\t')" read -r id screenshot; do
    [ -f "$screenshot" ] || { echo "missing campaign preview: $screenshot" >&2; exit 65; }
    # The card is deliberately a 512px thumbnail. Keep full-resolution art
    # in the downloadable package; a newly visible remote card must never
    # stall scrolling with a Retina-size decode/upload.
    /usr/bin/sips -s format jpeg -s formatOptions 92 \
        --resampleHeightWidthMax 512 "$screenshot" \
        --out "$destination_root/$id.jpg" >/dev/null
done
