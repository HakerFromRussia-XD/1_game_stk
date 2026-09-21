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
     "ctf=5 ghost-seed=5 status=ok"
