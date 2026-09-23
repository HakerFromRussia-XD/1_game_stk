#!/usr/bin/env ruby
# Frozen preflight for the curated Fluxara campaign.  It deliberately checks
# source resources only: a successful result says that an event is structurally
# launchable, not that it has passed the required Simulator runtime run.

require "rexml/document"
require "set"

root = File.expand_path("..", __dir__)
resources = File.join(root, "iosApp", "FluxaraResources")
manifest = File.join(resources, "fluxara-campaign.xml")
abort "missing campaign manifest: #{manifest}" unless File.file?(manifest)
ios_assets = ENV.fetch("IOS_ASSETS",
  File.join(root, "build-motorica-ios-assets", "assets", "data"))
music_root = File.join(ios_assets, "music")
shared_roots = [
  music_root,
  File.join(ios_assets, "textures"),
  File.join(ios_assets, "library"),
  File.join(ios_assets, "models")
].freeze

SUPPORTED = Set.new(%w[
  normal time_trial follow_leader lap_trial three_strikes free_for_all
  soccer capture_the_flag egg_hunt ghost_geometry
]).freeze
ARENA = Set.new(%w[three_strikes free_for_all]).freeze

def document(path)
  REXML::Document.new(File.read(path))
rescue REXML::ParseException => error
  abort "invalid XML #{path}: #{error.message.lines.first.strip}"
end

def track_attribute(track, name)
  track.root.attributes[name]
end

def has_yes_attribute?(track, name)
  track_attribute(track, name).to_s.casecmp("y").zero?
end

def scene_path(track_directory)
  ["scene.xml", "track.xml"].map { |name| File.join(track_directory, name) }
    .find { |path| File.file?(path) }
end

def resource_path(directory, resource, shared_roots = [])
  return false if resource.nil? || resource.empty?

  local = File.join(directory, resource)
  return local if File.file?(local)

  shared_roots.each do |root|
    direct = File.join(root, resource)
    return direct if File.file?(direct)

    found = Dir.glob(File.join(root, "**", resource)).find { |path| File.file?(path) }
    return found if found
  end
  nil
end

def scene_resources(scene, attribute, extensions)
  values = []
  scene.elements.each("//*") do |element|
    raw = element.attributes[attribute]
    next unless raw

    candidates = attribute == "texture" ? raw.split(/\s+/) : [raw]
    candidates.each do |value|
      values << value if extensions.include?(File.extname(value).downcase)
    end
  end
  values.uniq
end

def audit_scene_libraries(scene, track_directory, ios_assets, event_id, errors)
  pending = scene.elements.to_a("//library").map do |library|
    library.attributes["name"].to_s
  end
  visited_nodes = Set.new

  until pending.empty?
    name = pending.shift
    if name.empty?
      errors << "#{event_id}: library declaration has no name"
      next
    end

    # Track-local definitions take precedence in the runtime loader, then the
    # curated shared data/library snapshot.  Mirror that exact resolution
    # order so an iPhone-only realpath() abort cannot be hidden by the audit.
    local_node = File.join(track_directory, "library", name, "node.xml")
    shared_node = File.join(ios_assets, "library", name, "node.xml")
    node_path = if File.file?(local_node)
                  local_node
                elsif File.file?(shared_node)
                  shared_node
                end
    unless node_path
      errors << "#{event_id}: missing library node #{name}/node.xml"
      next
    end
    next unless visited_nodes.add?(node_path)

    document(node_path).elements.each("//library") do |nested|
      pending << nested.attributes["name"].to_s
    end
  end
end

def music_payload_exists?(music_path)
  music = document(music_path)
  payload = music.root.attributes["file"].to_s
  !payload.empty? && File.file?(File.join(File.dirname(music_path), payload))
end

campaign = document(manifest)
events = campaign.elements.to_a("campaign/event")
segments = campaign.elements.to_a("campaign/segment")
errors = []

errors << "expected 5 campaign segments, got #{segments.size}" unless segments.size == 5
segment_ids = segments.map { |segment| segment.attributes["id"] }
errors << "campaign segment IDs are missing or duplicated" unless
  segment_ids.all? { |id| id && !id.empty? } && segment_ids.uniq.size == segment_ids.size

ids = Set.new
tracks = Set.new
modes = Hash.new(0)
events.each do |event|
  id = event.attributes["id"].to_s
  mode = event.attributes["mode"].to_s
  track_id = event.attributes["track"].to_s
  segment = event.attributes["segment"].to_s
  if id.empty? || !ids.add?(id)
    errors << "event has missing or duplicate id: #{id.inspect}"
    next
  end
  errors << "#{id}: unsupported mode #{mode.inspect}" unless SUPPORTED.include?(mode)
  errors << "#{id}: unknown segment #{segment.inspect}" unless segment_ids.include?(segment)
  if track_id.empty? || !tracks.add?(track_id)
    errors << "#{id}: missing or duplicate track #{track_id.inspect}"
    next
  end
  modes[mode] += 1
  directory = File.join(resources, "tracks", track_id)
  track_path = File.join(directory, "track.xml")
  unless File.file?(track_path)
    errors << "#{id}: missing track.xml for #{track_id}"
    next
  end
  track = document(track_path)
  scene = scene_path(directory)
  screenshot = track_attribute(track, "screenshot").to_s
  errors << "#{id}: screenshot is missing" unless resource_path(directory, screenshot)

  music_name = track_attribute(track, "music").to_s
  music_path = resource_path(directory, music_name, [music_root])
  unless music_path
    errors << "#{id}: missing music declaration #{music_name.inspect}"
  else
    errors << "#{id}: music payload is missing for #{music_name}" unless
      music_payload_exists?(music_path)
  end

  if scene
    scene_document = document(scene)
    # A <library> can refer to another library from node.xml.  Check the
    # complete closure, not only direct scene references.
    audit_scene_libraries(scene_document, directory, ios_assets, id, errors)
    scene_resources(scene_document, "model", %w[.spm .b3d .obj]).each do |model|
      errors << "#{id}: scene model is missing: #{model}" unless
        resource_path(directory, model, shared_roots)
    end
    scene_resources(scene_document, "texture", %w[.png .jpg .jpeg .dds]).each do |texture|
      errors << "#{id}: scene texture is missing: #{texture}" unless
        resource_path(directory, texture, shared_roots)
    end
  else
    errors << "#{id}: scene declaration is missing"
  end

  case mode
  when *ARENA
    errors << "#{id}: arena flag missing" unless has_yes_attribute?(track, "arena")
    errors << "#{id}: arena navigation missing" unless File.file?(File.join(directory, "navmesh.xml"))
  when "soccer"
    errors << "#{id}: soccer flag missing" unless has_yes_attribute?(track, "soccer")
    errors << "#{id}: soccer navigation missing" unless File.file?(File.join(directory, "navmesh.xml"))
  when "capture_the_flag"
    errors << "#{id}: offline CTF declaration missing" unless
      event.attributes["requires-offline-ctf"] == "true"
    errors << "#{id}: CTF scene missing" unless scene
    next unless scene
    ctf_scene = document(scene)
    starts = ctf_scene.elements.to_a("//ctf-start").size
    red_flags = ctf_scene.elements.to_a("//red-flag").size
    blue_flags = ctf_scene.elements.to_a("//blue-flag").size
    errors << "#{id}: only #{starts} CTF starts for player plus six opponents" if starts < 7
    errors << "#{id}: CTF flags red=#{red_flags} blue=#{blue_flags}" unless
      red_flags.positive? && blue_flags.positive?
  when "egg_hunt"
    errors << "#{id}: egg placement missing" unless File.file?(File.join(directory, "easter_eggs.xml"))
  when "ghost_geometry"
    errors << "#{id}: replay seed declaration missing" unless event.attributes["requires-replay"] == "true"
  end
end

errors << "expected 50 events, got #{events.size}" unless events.size == 50
errors << "expected 50 unique tracks, got #{tracks.size}" unless tracks.size == 50
SUPPORTED.each do |mode|
  errors << "expected five #{mode} events, got #{modes[mode]}" unless modes[mode] == 5
end

karts = Dir.glob(File.join(resources, "karts", "fluxara-*"))
  .count { |path| File.directory?(path) }
errors << "expected 15 Fluxara karts, got #{karts}" unless karts == 15

Dir.glob(File.join(resources, "karts", "fluxara-*", "kart.xml")).sort.each do |kart_path|
  kart = document(kart_path)
  directory = File.dirname(kart_path)
  name = File.basename(directory)
  %w[model-file icon-file minimap-icon-file].each do |attribute|
    resource = kart.root.attributes[attribute].to_s
    errors << "#{name}: missing #{attribute}" if resource.empty?
    errors << "#{name}: missing #{attribute} resource #{resource}" unless
      resource.empty? || resource_path(directory, resource, shared_roots)
  end
end

source = File.read(File.join(root, "src", "states_screens", "fluxara_event.hpp"))
errors << "offline CTF opponents are disabled" unless
  source.include?("mode!=\"ghost_geometry\" && mode!=\"egg_hunt\"")
profile = File.read(File.join(root, "src", "config", "player_profile.cpp"))
errors << "CTF draw can still award a campaign cup" unless
  profile.include?("ctf->getRedScore() > ctf->getBlueScore()")
errors << "soccer draw can still award a campaign cup" unless
  profile.include?("soccer->getScore(KART_TEAM_RED) >")
errors << "FFA tie can still award a campaign cup" unless
  profile.include?("tied_for_first == 1")

unless errors.empty?
  warn errors.join("\n")
  exit 65
end

puts "FLUXARA_CAMPAIGN_STATIC_AUDIT events=#{events.size} tracks=#{tracks.size} " \
    "karts=#{karts} modes=#{modes.sort.map { |mode, count| "#{mode}:#{count}" }.join(',')} " \
    "ctf=5 ghost-seed=5 resources=track-preview-music-scene-kart status=ok"
