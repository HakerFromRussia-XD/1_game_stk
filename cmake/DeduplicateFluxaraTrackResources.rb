#!/usr/bin/env ruby
# frozen_string_literal: true

# Moves byte-identical, root-level track resources into the engine's existing
# shared resource directories.  FLUXARA_DRIFT already searches data/textures and
# data/sfx after a track-local directory, so no gameplay XML needs rewriting.
# Music descriptors use the existing Track::getMusicInformation fallback to
# data/music when their local copy is absent.

require 'digest'
require 'fileutils'

abort "usage: #{$PROGRAM_NAME} <Fluxara Drift.app>" unless ARGV.length == 1

bundle = File.expand_path(ARGV.fetch(0))
data = File.join(bundle, 'data')
tracks_root = File.join(data, 'tracks')
abort "missing tracks directory: #{tracks_root}" unless Dir.exist?(tracks_root)

IMAGE_EXTENSIONS = %w[.png .jpg .jpeg .dds].freeze
SFX_EXTENSIONS = %w[.ogg .wav].freeze
# Do not move track models into data/models.  TrackObjectPresentation opens
# scene model references through Irrlicht's mounted per-track archive; paths
# containing "../../models" are not resolved through that virtual archive on
# the iOS Vulkan build.  The apparent saving is normally only a few KiB, while
# a shared model (for example bumper.spm) then aborts the entire event load.
# Keep all models next to their scene.xml files so the runtime lookup is exact.
MODEL_EXTENSIONS = %w[.spm .b3d .obj].freeze
RESOURCE_EXTENSIONS = (IMAGE_EXTENSIONS + SFX_EXTENSIONS).freeze

def digest(path)
  Digest::SHA256.file(path).hexdigest
end

def same_file?(left, right)
  File.file?(left) && File.size(left) == File.size(right) && digest(left) == digest(right)
end

def claim_destination(source, destination)
  if File.exist?(destination)
    return :ok if same_file?(source, destination)

    return :conflict
  end

  FileUtils.mkdir_p(File.dirname(destination))
  FileUtils.cp(source, destination, preserve: true)
  same_file?(source, destination) ? :ok : :copy_failed
end

def music_descriptor_for(audio_path)
  stem = File.basename(audio_path, File.extname(audio_path))
  descriptor = File.join(File.dirname(audio_path), "#{stem}.music")
  return nil unless File.file?(descriptor)

  xml = File.binread(descriptor)
  return nil unless xml =~ /\bfile\s*=\s*[\"']#{Regexp.escape(File.basename(audio_path))}[\"']/

  descriptor
end

def relative_to(path, root)
  path.sub(/\A#{Regexp.escape(root)}\//, '')
end

def rewrite_scene_model_reference(track_dir, basename)
  scene = File.join(track_dir, 'scene.xml')
  return false unless File.file?(scene)

  original = File.binread(scene)
  updated = original.gsub(/(\bmodel\s*=\s*[\"'])#{Regexp.escape(basename)}([\"'])/, "\\1../../models/#{basename}\\2")
  return false if updated == original

  File.binwrite(scene, updated)
  true
end

def scene_model_reference?(track_dir, basename)
  scene = File.join(track_dir, 'scene.xml')
  return false unless File.file?(scene)

  File.binread(scene) =~ /\bmodel\s*=\s*[\"']#{Regexp.escape(basename)}[\"']/
end

track_dirs = []
Dir.children(tracks_root).sort.each do |name|
  path = File.join(tracks_root, name)
  track_dirs << path if name.start_with?('fluxara-') && File.directory?(path)
end

groups = Hash.new { |hash, key| hash[key] = [] }
track_dirs.each do |track_dir|
  Dir.children(track_dir).sort.each do |name|
    path = File.join(track_dir, name)
    next unless File.file?(path)
    next if name.start_with?('screenshot.') # Track previews remain track-local.

    extension = File.extname(name).downcase
    next unless RESOURCE_EXTENSIONS.include?(extension)

    groups[[File.basename(path), File.size(path), digest(path)]] << path
  end
end

summary = Hash.new(0)
manifest = ["type\tsha256\tbytes\tshared_path\tremoved_track_paths"]

groups.each do |(basename, bytes, sha256), paths|
  next if paths.length < 2

  extension = File.extname(basename).downcase
  type = if IMAGE_EXTENSIONS.include?(extension)
           :texture
         elsif SFX_EXTENSIONS.include?(extension)
           :audio
         end
  next unless type

  descriptor_paths = []
  destination = nil
  manifest_type = type.to_s
  if type == :texture
    destination = File.join(data, 'textures', basename)
  elsif type == :model
    # Track scene models are loaded by joining their name to m_root, so change
    # only proven scene.xml model attributes to the global data/models copy.
    # Do not move a model whose references cannot all be rewritten safely.
    unless paths.all? { |path| scene_model_reference?(File.dirname(path), basename) }
      summary[:skipped_model_reference] += (paths.length - 1) * bytes
      next
    end
    destination = File.join(data, 'models', basename)
  else
    candidate_descriptors = paths.map { |path| music_descriptor_for(path) }
    if candidate_descriptors.all?
      descriptor_hashes = candidate_descriptors.map { |path| [File.size(path), digest(path)] }.uniq
      if descriptor_hashes.length != 1
        summary[:skipped_music_metadata] += (paths.length - 1) * bytes
        next
      end

      descriptor_paths = candidate_descriptors
      destination = File.join(data, 'music', basename)
      descriptor_destination = File.join(data, 'music', File.basename(descriptor_paths.first))
      unless claim_destination(descriptor_paths.first, descriptor_destination) == :ok
        summary[:skipped_destination_conflict] += (paths.length - 1) * bytes
        next
      end
      manifest_type = 'music'
    else
      destination = File.join(data, 'sfx', basename)
      manifest_type = 'sfx'
    end
  end

  destination_status = claim_destination(paths.first, destination)
  unless destination_status == :ok
    summary[:skipped_destination_conflict] += (paths.length - 1) * bytes
    next
  end

  if type == :model
    rewritten = paths.all? { |path| rewrite_scene_model_reference(File.dirname(path), basename) }
    raise "could not rewrite shared model references for #{basename}" unless rewritten
  end

  paths.each { |path| File.delete(path) }
  descriptor_paths.each { |path| File.delete(path) }
  saved = (paths.length - 1) * bytes
  summary[:saved_bytes] += saved
  summary["#{manifest_type}_bytes".to_sym] += saved
  summary["#{manifest_type}_groups".to_sym] += 1
  manifest << [manifest_type, sha256, bytes, relative_to(destination, data),
               paths.map { |path| relative_to(path, data) }.join('|')].join("\t")
end

manifest_path = File.join(data, 'fluxara-track-dedup.tsv')
File.write(manifest_path, manifest.join("\n") + "\n")

puts [
  'FLUXARA_TRACK_DEDUP',
  "texture_groups=#{summary[:texture_groups]}",
  "texture_saved_bytes=#{summary[:texture_bytes]}",
  "sfx_groups=#{summary[:sfx_groups]}",
  "sfx_saved_bytes=#{summary[:sfx_bytes]}",
  "music_groups=#{summary[:music_groups]}",
  "music_saved_bytes=#{summary[:music_bytes]}",
  "model_groups=#{summary[:model_groups]}",
  "model_saved_bytes=#{summary[:model_bytes]}",
  "skipped_bytes=#{summary[:skipped_destination_conflict] + summary[:skipped_music_metadata] + summary[:skipped_model_reference]}",
  "saved_bytes=#{summary[:saved_bytes]}"
].join(' ')
