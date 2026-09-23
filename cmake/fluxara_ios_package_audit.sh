#!/bin/sh
# Verifies that the iOS bundle contains the curated Fluxara runtime payload.
# It does not build, install, or select a run destination.
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <Fluxara Drift.app>" >&2
    exit 64
fi

bundle="$1"
data="$bundle/data"
hud="$data/gui/fluxara/hud"

[ -d "$data" ] || { echo "missing bundle data: $data" >&2; exit 66; }
[ -d "$hud" ] || { echo "missing Fluxara HUD: $hud" >&2; exit 66; }
[ -f "$data/fluxaradrift.git" ] || {
    echo "missing required FluxaraDrift data marker" >&2
    exit 65
}
for runtime_file in graphical_restrictions.xml official_karts.xml
do
    [ -f "$data/$runtime_file" ] || {
        echo "missing required iOS runtime file: $runtime_file" >&2
        exit 65
    }
done
for runtime_dir in challenges grandprix replay packaged-scripts ttf
do
    [ -d "$data/$runtime_dir" ] || {
        echo "missing required iOS runtime directory: $runtime_dir" >&2
        exit 65
    }
done

locales=$(find "$data/po" -maxdepth 1 -type f -name '*.po' -exec basename {} \; | sort | tr '\n' ' ')
[ "$locales" = "ru.po " ] || {
    echo "expected only Russian localization plus English fallback, found: $locales" >&2
    exit 65
}
[ -f "$data/ttf/Cantarell-Regular.otf" ] && [ -f "$data/ttf/SigmarOne.otf" ] || {
    echo "missing required Fluxara base fonts" >&2
    exit 65
}
grep -q '<fonts-list normal-ttf="Cantarell-Regular.otf" digit-ttf="SigmarOne.otf"/>' \
    "$data/fluxara_drift_config.xml" || {
    echo "fluxara_drift_config still references excluded fallback fonts" >&2
    exit 65
}
extra_base_font=$(find "$data/ttf" -maxdepth 1 -type f \
    ! -name 'Cantarell-Regular.otf' ! -name 'SigmarOne.otf' -print -quit)
[ -z "$extra_base_font" ] || {
    echo "unapproved upstream fallback font remains in iOS bundle: $extra_base_font" >&2
    exit 65
}
[ -f "$data/skins/fluxara/data/ttf/Baloo2-ExtraBold-BalooCyrillic.ttf" ] || {
    echo "missing required Fluxara Cyrillic font" >&2
    exit 65
}

for asset in \
    steering-wheel.png accelerator.png throttle-pedal.png pause.png \
    nitro.png nitro-empty.png mirror.png reset.png drift.png \
    halo-idle.png halo-pressed.png counter-small.png counter-time.png \
    minimap-panel.png up.png down.png screen-other.png \
    bonus-zipper.png bonus-bowling.png bonus-bubblegum.png bonus-cake.png \
    bonus-anchor.png bonus-swap.png bonus-swatter.png bonus-rubber-ball.png \
    bonus-parachute.png bonus-plunger.png
do
    [ -f "$hud/$asset" ] || {
        echo "missing approved HUD asset: $asset" >&2
        exit 65
    }
done

if find "$data" \( -iname '*motorica*.fluxara_driftgui' -o -iname '*signal*lab*' \
    -o -path '*/challenges/motorica_*' \) -print -quit | grep -q .
then
    echo "legacy Motorica content remains in iOS bundle" >&2
    exit 65
fi

if [ -d "$data/gui/icons/android" ]; then
    echo "legacy Android FLUXARA_DRIFT HUD masks remain in iOS bundle" >&2
    exit 65
fi

for retired_dir in \
    "$data/gui/screens/help" \
    "$data/gui/screens/online" \
    "$data/gui/screens/options" \
    "$data/gui/dialogs/online" \
    "$data/gui/icons/online"
do
    [ ! -d "$retired_dir" ] || {
        echo "retired FLUXARA_DRIFT UI remains in iOS bundle: $retired_dir" >&2
        exit 65
    }
done

# Fluxara provides the complete public flow.  Keeping upstream .fluxara_driftgui files
# in the product makes the retired FLUXARA_DRIFT menus an accidental fallback and is not
# a successful UI cleanup even when the normal route does not open them.
legacy_screen=$(find "$data/gui/screens" -maxdepth 1 -type f -name '*.fluxara_driftgui' \
    ! -name 'fluxara_*.fluxara_driftgui' -print -quit)
[ -z "$legacy_screen" ] || {
    echo "legacy FLUXARA_DRIFT screen remains in iOS bundle: $legacy_screen" >&2
    exit 65
}
fluxara_screens=$(find "$data/gui/screens" -maxdepth 1 -type f \
    -name 'fluxara_*.fluxara_driftgui' | wc -l | tr -d ' ')
[ "$fluxara_screens" = 6 ] || {
    echo "expected 6 Fluxara screens, found $fluxara_screens" >&2
    exit 65
}

tracks=$(find "$data/tracks" -mindepth 1 -maxdepth 1 -type d -name 'fluxara-*' | wc -l | tr -d ' ')
karts=$(find "$data/karts" -mindepth 1 -maxdepth 1 -type d -name 'fluxara-*' | wc -l | tr -d ' ')
[ -f "$data/fluxara-campaign.xml" ] || {
    echo "missing Fluxara campaign manifest" >&2
    exit 65
}
campaign_tracks=$(/usr/bin/ruby -rrexml/document -e '
    campaign = REXML::Document.new(File.read(ARGV.fetch(0)))
    puts campaign.elements.to_a("campaign/event").map { |event| event.attributes["track"] }.uniq.sort
' "$data/fluxara-campaign.xml")
campaign_track_count=$(printf '%s\n' "$campaign_tracks" | sed '/^$/d' | wc -l | tr -d ' ')
[ "$campaign_track_count" = 50 ] || {
    echo "expected 50 unique Fluxara campaign tracks, found $campaign_track_count" >&2
    exit 65
}
for track in $campaign_tracks; do
    [ -d "$data/tracks/$track" ] || {
        echo "campaign track is missing from bundle: $track" >&2
        exit 65
    }
done
[ "$karts" = 15 ] || { echo "expected 15 Fluxara karts, found $karts" >&2; exit 65; }

garage="$data/gui/fluxara/home"
[ -f "$garage/garage-background-figma-outpaint-v1.png" ] || {
    echo "missing approved garage background" >&2
    exit 65
}
for retired_garage_asset in \
    garage-background.png garage-background-figma.png \
    garage-background-outpaint-v1.png garage-background-outpaint-v2.png \
    garage-floor-extension-v1.png
do
    [ ! -e "$garage/$retired_garage_asset" ] || {
        echo "historical garage asset remains in iOS bundle: $retired_garage_asset" >&2
        exit 65
    }
done

authoring_file=$(find "$data" -type f \( \
    -name '*.xcf' -o -name '*.pot' -o -name '*.py' -o -name '*.sh' \
    -o -name '*.md' -o -name '*.desktop' -o -name '*.metainfo.xml' \
\) -print -quit)
[ -z "$authoring_file" ] || {
    echo "non-runtime authoring file remains in iOS bundle: $authoring_file" >&2
    exit 65
}

# GUIEngine reads the configured fallback faces before the Fluxara skin has a
# chance to prepend its own font.  A pruned iOS bundle with a stale font list
# therefore dies at startup in FileManager::getAssetChecked.  Keep this check
# beside the package audit so a missing skin/font is a build failure, not a
# device crash report.
for required_gui_asset in \
    skins/classic/fluxara_driftskin.xml \
    skins/fluxara/fluxara_driftskin.xml \
    ttf/Cantarell-Regular.otf \
    ttf/SigmarOne.otf \
    skins/fluxara/data/ttf/Baloo2-ExtraBold-BalooCyrillic.ttf
do
    [ -f "$data/$required_gui_asset" ] || {
        echo "missing required Fluxara GUI asset: $required_gui_asset" >&2
        exit 65
    }
done
grep -F 'normal-ttf="Cantarell-Regular.otf"' "$data/fluxara_drift_config.xml" >/dev/null || {
    echo "iOS font allowlist did not rewrite fluxara_drift_config.xml" >&2
    exit 65
}
grep -F 'digit-ttf="SigmarOne.otf"' "$data/fluxara_drift_config.xml" >/dev/null || {
    echo "iOS digit font allowlist did not rewrite fluxara_drift_config.xml" >&2
    exit 65
}

dedup_manifest="$data/fluxara-track-dedup.tsv"
[ -f "$dedup_manifest" ] || {
    echo "missing Fluxara track deduplication manifest" >&2
    exit 65
}
dedup_rows=$(awk 'END { print NR - 1 }' "$dedup_manifest")
[ "$dedup_rows" -gt 0 ] || {
    echo "track deduplication found no removable exact duplicates" >&2
    exit 65
}
dedup_saved_bytes=$(awk -F '\t' 'NR > 1 { sum += ($3 * split($5, paths, "\\|") - $3) } END { print sum + 0 }' "$dedup_manifest")
[ "$dedup_saved_bytes" -gt 0 ] || {
    echo "track deduplication manifest reports no saved bytes" >&2
    exit 65
}

# The manifest is part of the runtime contract, not a report-only artifact:
# every claimed shared object must be byte-identical to its recorded digest,
# every old track-local copy must be gone, and moved scene models must point
# at the common models directory.
while IFS="$(printf '\t')" read -r type sha256 _bytes shared_path removed_paths
do
    [ "$type" = "type" ] && continue
    shared="$data/$shared_path"
    [ -f "$shared" ] || {
        [ "$type" = "sfx" ] || [ "$type" = "music" ] || {
            echo "deduplicated resource is missing: $shared_path" >&2
            exit 65
        }
    }
    case "$type" in
        texture)
            if [ "${FLUXARA_IOS_EXPECT_ASTC:-0}" = 1 ]; then
                file "$shared" | grep -q 'ASTC 6x6 texture' || {
                    # Tiny or already smaller PNG/JPG assets intentionally
                    # stay in their original container; only accept them when
                    # the payload still equals the manifest source digest.
                    actual_sha256=$(shasum -a 256 "$shared" | awk '{ print $1 }')
                    [ "$actual_sha256" = "$sha256" ] || {
                        echo "deduplicated texture is neither ASTC nor its original payload: $shared_path" >&2
                        exit 65
                    }
                }
            else
                actual_sha256=$(shasum -a 256 "$shared" | awk '{ print $1 }')
                [ "$actual_sha256" = "$sha256" ] || {
                    echo "deduplicated resource digest mismatch: $shared_path" >&2
                    exit 65
                }
            fi
            ;;
        sfx|music)
            if [ "${FLUXARA_IOS_EXPECT_OPUS:-0}" = 1 ]; then
                opus_resource=${shared%.*}.opus
                if [ -f "$opus_resource" ]; then
                    file "$opus_resource" | grep -q 'Opus audio' || {
                        echo "deduplicated audio is not valid Opus: $shared_path" >&2
                        exit 65
                    }
                    runtime_audio_name=${opus_resource##*/}
                else
                    # Keep OGG where Opus would be larger; this is recorded
                    # as an explicit retained decision in its audio manifest.
                    actual_sha256=$(shasum -a 256 "$shared" | awk '{ print $1 }')
                    [ "$actual_sha256" = "$sha256" ] || {
                        echo "deduplicated retained OGG digest mismatch: $shared_path" >&2
                        exit 65
                    }
                    runtime_audio_name=${shared##*/}
                fi
            else
                actual_sha256=$(shasum -a 256 "$shared" | awk '{ print $1 }')
                [ "$actual_sha256" = "$sha256" ] || {
                    echo "deduplicated resource digest mismatch: $shared_path" >&2
                    exit 65
                }
            fi
            ;;
        *)
            actual_sha256=$(shasum -a 256 "$shared" | awk '{ print $1 }')
            [ "$actual_sha256" = "$sha256" ] || {
                echo "deduplicated resource digest mismatch: $shared_path" >&2
                exit 65
            }
            ;;
    esac
    old_ifs=$IFS
    IFS='|'
    for removed_path in $removed_paths
    do
        IFS=$old_ifs
        [ ! -e "$data/$removed_path" ] || {
            echo "track-local duplicate remains: $removed_path" >&2
            exit 65
        }
        if [ "$type" = "model" ]; then
            scene="${data}/${removed_path%/*}/scene.xml"
            model_name=${shared_path##*/}
            grep -F "../../models/$model_name" "$scene" >/dev/null || {
                echo "deduplicated scene model was not repointed: $removed_path" >&2
                exit 65
            }
        fi
        IFS='|'
    done
    IFS=$old_ifs
    if [ "$type" = "music" ]; then
        music_descriptor=${shared_path%.*}.music
        [ -f "$data/$music_descriptor" ] || {
            echo "deduplicated music descriptor is missing: $music_descriptor" >&2
            exit 65
        }
        if [ "${FLUXARA_IOS_EXPECT_OPUS:-0}" = 1 ]; then
            ogg_name=${shared_path##*/}
            opus_name=${ogg_name%.*}.opus
            grep -F "$runtime_audio_name" "$data/$music_descriptor" >/dev/null || {
                echo "deduplicated music descriptor does not refer to its runtime audio: $music_descriptor" >&2
                exit 65
            }
            if [ "$runtime_audio_name" = "$opus_name" ]; then
                grep -F "$ogg_name" "$data/$music_descriptor" >/dev/null && {
                    echo "deduplicated music descriptor still refers to OGG: $music_descriptor" >&2
                    exit 65
                }
            fi
        fi
    fi
done < "$dedup_manifest"

if [ "${FLUXARA_IOS_EXPECT_ASTC:-0}" = 1 ]; then
    astc_manifest="$data/fluxara-ios-astc.tsv"
    [ -f "$astc_manifest" ] || {
        echo "missing iOS ASTC manifest" >&2
        exit 65
    }
    astc_rows=$(awk 'END { print NR - 1 }' "$astc_manifest")
    [ "$astc_rows" -gt 0 ] || {
        echo "ASTC packaging converted no gameplay texture" >&2
        exit 65
    }
    astc_saved_bytes=$(awk -F '\t' 'NR > 1 { sum += $2 - $3 } END { print sum + 0 }' "$astc_manifest")
    [ "$astc_saved_bytes" -gt 0 ] || {
        echo "ASTC manifest reports no saved bytes" >&2
        exit 65
    }
    # Every raw ASTC payload is loaded straight by GEVulkanTexture.  Validate
    # every converted file, rather than merely counting manifest rows: a
    # malformed payload in any one of the 50 tracks used to surface only when
    # that particular track was opened on iPhone.
    astc_validation=$(/usr/bin/ruby -e '
      data, manifest = ARGV
      magic = [0x13, 0xab, 0xa1, 0x5c].pack("C*")
      rows = File.readlines(manifest, chomp: true).drop(1).map do |line|
        _sha, _original, _compressed, path = line.split("\t", 4)
        abort "invalid ASTC manifest row: #{line}" if path.nil? || path.empty?
        abort "unsafe ASTC manifest path: #{path}" if path.start_with?("/") || path.split("/").include?("..")
        path
      end
      abort "duplicate ASTC manifest path" unless rows.uniq.size == rows.size
      manifest_paths = rows.to_h { |path| [path, true] }
      seen_astc = {}
      rows.each do |path|
        full = File.join(data, path)
        abort "ASTC file missing: #{path}" unless File.file?(full)
        size = File.size(full)
        abort "ASTC file is too small: #{path}" if size < 16
        header = File.binread(full, 16)
        abort "ASTC header is invalid: #{path}" unless header.start_with?(magic) &&
          header.getbyte(4) == 6 && header.getbyte(5) == 6 && header.getbyte(6) == 1
        width = header.getbyte(7) | (header.getbyte(8) << 8) | (header.getbyte(9) << 16)
        height = header.getbyte(10) | (header.getbyte(11) << 8) | (header.getbyte(12) << 16)
        depth = header.getbyte(13) | (header.getbyte(14) << 8) | (header.getbyte(15) << 16)
        abort "ASTC dimensions are invalid: #{path}" if width.zero? || height.zero? || depth != 1
        expected = 16 + ((width + 5) / 6) * ((height + 5) / 6) * 16
        abort "ASTC payload size is invalid: #{path}" unless size == expected
        seen_astc[path] = true
      end
      Dir.glob(File.join(data, "{tracks,textures}", "**", "*")).each do |full|
        next unless File.file?(full) && File.size(full) >= 4
        next unless File.binread(full, 4) == magic
        path = full.delete_prefix(data + "/")
        abort "untracked raw ASTC texture: #{path}" unless manifest_paths[path]
      end
      tracks = rows.map { |path| path[%r{\\Atracks/(fluxara-[^/]+)/}, 1] }.compact.uniq
      puts "files=#{rows.size} tracks=#{tracks.size}"
    ' "$data" "$astc_manifest") || exit 65
else
    astc_rows=0
    astc_saved_bytes=0
    astc_validation="files=0 tracks=0"
fi

# Scene XML only names meshes; their binary headers are parsed later while a
# race is loading.  Validate all bundled track/shared meshes now, so a bad
# copy cannot crash or abort a single track at runtime.
model_validation=$(/usr/bin/ruby -e '
  data = ARGV.fetch(0)
  files = Dir.glob(File.join(data, "{tracks,models}", "**", "*"))
             .select { |path| File.file?(path) && %w[.spm .b3d].include?(File.extname(path).downcase) }
  abort "no track models in bundle" if files.empty?
  counts = Hash.new(0)
  files.each do |path|
    ext = File.extname(path).downcase
    header = File.binread(path, ext == ".spm" ? 4 : 8)
    case ext
    when ".spm"
      abort "truncated SPM mesh: #{path}" unless header.bytesize == 4
      abort "invalid SPM mesh header: #{path}" unless header.byteslice(0, 2) == "SP" && (header.getbyte(2) >> 3) == 1
    when ".b3d"
      abort "truncated B3D mesh: #{path}" unless header.bytesize == 8
      abort "invalid B3D mesh header: #{path}" unless header.byteslice(0, 4) == "BB3D"
    end
    counts[ext] += 1
  end
  puts "spm=#{counts[".spm"]} b3d=#{counts[".b3d"]}"
' "$data") || exit 65

# Materials use FileManager::searchModel for terrain SFX first and then the
# Fluxara iOS shared-SFX fallback.  A missing target used to throw while a
# single affected circuit was loading.  Verify every reference now, across all
# bundled tracks, including references repointed to data/sfx by deduplication.
material_sfx_validation=$(/usr/bin/ruby -rrexml/document -rrexml/xpath -e '
  data = File.expand_path(ARGV.fetch(0))
  errors = []
  references = 0
  Dir.glob(File.join(data, "tracks", "fluxara-*", "materials.xml")).sort.each do |materials|
    document = REXML::Document.new(File.binread(materials))
    REXML::XPath.each(document, "//sfx") do |node|
      filename = node.attributes["filename"].to_s
      next if filename.empty?
      references += 1
      if filename.start_with?("/") || filename.split("/").include?("..") && !filename.start_with?("../../sfx/")
        errors << "unsafe terrain SFX path #{materials}: #{filename}"
        next
      end
      local = File.expand_path(File.join(File.dirname(materials), filename))
      shared = File.join(data, "sfx", File.basename(filename))
      unless local.start_with?(data + "/") && (File.file?(local) || File.file?(shared))
        errors << "missing terrain SFX #{materials}: #{filename}"
      end
    end
  end
  abort errors.join("\n") unless errors.empty?
  puts "references=#{references}"
' "$data") || exit 65

if [ "${FLUXARA_IOS_EXPECT_OPUS:-0}" = 1 ]; then
    opus_manifest="$data/fluxara-ios-opus.tsv"
    [ -f "$opus_manifest" ] || {
        echo "missing iOS Opus manifest" >&2
        exit 65
    }
    opus_rows=$(awk -F '\t' 'NR > 1 && $1 == "opus" { count++ } END { print count + 0 }' "$opus_manifest")
    [ "$opus_rows" -gt 0 ] || {
        echo "Opus packaging converted no audio" >&2
        exit 65
    }
    opus_saved_bytes=$(awk -F '\t' 'NR > 1 && $1 == "opus" { sum += $2 - $3 } END { print sum + 0 }' "$opus_manifest")
    retained_ogg=$(awk -F '\t' 'NR > 1 && $1 == "ogg" { count++ } END { print count + 0 }' "$opus_manifest")
    remaining_ogg=$(find "$data" -type f -name '*.ogg' | wc -l | tr -d ' ')
    [ "$remaining_ogg" = "$retained_ogg" ] || {
        echo "unaccounted OGG remains in iOS bundle: files=$remaining_ogg manifest=$retained_ogg" >&2
        exit 65
    }
else
    opus_rows=0
    opus_saved_bytes=0
fi

echo "FLUXARA_IOS_PACKAGE_AUDIT hud=27 screens=$fluxara_screens tracks=$tracks campaign-tracks=$campaign_track_count karts=$karts locales=ru,en-fallback dedup-rows=$dedup_rows dedup-saved-bytes=$dedup_saved_bytes astc-rows=$astc_rows astc-saved-bytes=$astc_saved_bytes astc-validated=$astc_validation models-validated=$model_validation terrain-sfx-validated=$material_sfx_validation opus-rows=$opus_rows opus-saved-bytes=$opus_saved_bytes retired-ogg=${retained_ogg:-0} retired-ui=0 bundle=$bundle"
