#!/usr/bin/env ruby
# frozen_string_literal: true

# Converts only gameplay track textures to raw ASTC 6x6 for the iOS GLES2
# loader. The original filenames stay intact because mesh/material references
# are name-based. Output is cached by source digest outside the source tree.

require 'digest'
require 'fileutils'

abort "usage: #{$PROGRAM_NAME} <Fluxara Drift.app> <astcenc> <cache-dir>" unless ARGV.length == 3

bundle, encoder, cache_root = ARGV.map { |value| File.expand_path(value) }
data = File.join(bundle, 'data')
tracks_root = File.join(data, 'tracks')
abort "missing app data: #{data}" unless Dir.exist?(data)
abort "missing track data: #{tracks_root}" unless Dir.exist?(tracks_root)
abort "missing ASTC encoder: #{encoder}" unless File.executable?(encoder)

ASTC_MAGIC = [0x13, 0xab, 0xa1, 0x5c].pack('C*').freeze
IMAGE_EXTENSIONS = %w[.png .jpg .jpeg].freeze
ASTC_PRESET = ENV.fetch('FLUXARA_ASTC_PRESET', 'fast').freeze
abort "unsupported ASTC preset: #{ASTC_PRESET}" unless %w[fast medium thorough exhaustive].include?(ASTC_PRESET)

def track_preview_paths(tracks_root)
  excluded = []
  Dir.children(tracks_root).each do |name|
    track_dir = File.join(tracks_root, name)
    next unless name.start_with?('fluxara-') && File.directory?(track_dir)

    track_xml = File.join(track_dir, 'track.xml')
    next unless File.file?(track_xml)

    match = File.binread(track_xml).match(/\bscreenshot\s*=\s*[\"']([^\"']+)[\"']/)
    excluded << File.expand_path(File.join(track_dir, match[1])) if match
  end
  excluded
end

def valid_astc?(path)
  return false unless File.file?(path) && File.size(path) >= 16

  header = File.binread(path, 16)
  return false unless header.start_with?(ASTC_MAGIC)
  return false unless header.getbyte(4) == 6 && header.getbyte(5) == 6 && header.getbyte(6) == 1

  width = header.getbyte(7) | (header.getbyte(8) << 8) | (header.getbyte(9) << 16)
  height = header.getbyte(10) | (header.getbyte(11) << 8) | (header.getbyte(12) << 16)
  depth = header.getbyte(13) | (header.getbyte(14) << 8) | (header.getbyte(15) << 16)
  return false if width.zero? || height.zero? || depth != 1

  File.size(path) == 16 + ((width + 5) / 6) * ((height + 5) / 6) * 16
end

def astc_size(width, height)
  ((width + 5) / 6) * ((height + 5) / 6) * 16 + 16
end

# Avoid sending already-more-compact JPEG/PNG files through astcenc. Raw ASTC
# has a deterministic 6x6 payload size, so the decision is lossless and can
# be made from the source header before a costly encoder process is spawned.
def image_dimensions(path)
  header = File.binread(path, 32)
  if header.start_with?("\x89PNG\r\n\x1a\n".b) && header.bytesize >= 24
    return header.byteslice(16, 4).unpack1('N'), header.byteslice(20, 4).unpack1('N')
  end
  return nil unless header.start_with?("\xff\xd8".b)

  bytes = File.binread(path)
  offset = 2
  while offset + 9 < bytes.bytesize
    offset += 1 while offset < bytes.bytesize && bytes.getbyte(offset) != 0xff
    offset += 1 while offset < bytes.bytesize && bytes.getbyte(offset) == 0xff
    break if offset >= bytes.bytesize

    marker = bytes.getbyte(offset)
    offset += 1
    next if marker == 0x01 || (0xd0..0xd9).cover?(marker)
    break if offset + 1 >= bytes.bytesize

    segment_length = bytes.byteslice(offset, 2).unpack1('n')
    break if segment_length < 2 || offset + segment_length > bytes.bytesize
    if ((0xc0..0xc3).cover?(marker) || (0xc5..0xc7).cover?(marker) ||
        (0xc9..0xcb).cover?(marker) || (0xcd..0xcf).cover?(marker)) && segment_length >= 8
      height = bytes.byteslice(offset + 3, 2).unpack1('n')
      width = bytes.byteslice(offset + 5, 2).unpack1('n')
      return width, height if width.positive? && height.positive?
    end
    offset += segment_length
  end
  nil
end

def relative_to(path, root)
  path.sub(/\A#{Regexp.escape(root)}\//, '')
end

excluded = track_preview_paths(tracks_root)
targets = Dir.glob(File.join(tracks_root, '**', '*')).select do |path|
  File.file?(path) && IMAGE_EXTENSIONS.include?(File.extname(path).downcase) &&
    !excluded.include?(File.expand_path(path))
end

# Track resources deduplicated into data/textures remain gameplay textures and
# must use the same mobile representation. The manifest lists only content
# originally taken from Fluxara track directories.
dedup_manifest = File.join(data, 'fluxara-track-dedup.tsv')
if File.file?(dedup_manifest)
  File.readlines(dedup_manifest).drop(1).each do |line|
    type, _sha, _bytes, shared_path, = line.split("\t", 5)
    next unless type == 'texture'

    path = File.join(data, shared_path)
    targets << path if File.file?(path) && IMAGE_EXTENSIONS.include?(File.extname(path).downcase)
  end
end
targets.uniq!

cache_dir = File.join(cache_root, "astc-6x6-#{ASTC_PRESET}")
FileUtils.mkdir_p(cache_dir)
manifest = ["sha256\toriginal_bytes\tastc_bytes\tpath"]
summary = Hash.new(0)

# Hash once and encode each distinct payload once. Parallel workers only write
# unique cache paths, so an interrupted packaging run never corrupts a source
# texture and the next run reuses every completed result.
entries = targets.sort.map do |source|
  original_bytes = File.size(source)
  next if original_bytes < 4096
  dimensions = image_dimensions(source)
  next if dimensions && astc_size(*dimensions) >= original_bytes

  sha256 = Digest::SHA256.file(source).hexdigest
  [source, sha256, File.join(cache_dir, "#{sha256}.astc")]
end.compact

jobs = {}
entries.each do |source, sha256, cached|
  jobs[sha256] ||= [source, cached]
end
pending = jobs.reject { |_sha256, (_source, cached)| valid_astc?(cached) }
worker_count = ENV.fetch('FLUXARA_ASTC_JOBS', '6').to_i
worker_count = 1 if worker_count < 1
encoder_threads = 1

# Most of the package benefits from one ASTC thread per parallel image. Near
# the end only one or a few large images can remain; leaving each at -j 1 then
# turns that tail into a several-minute serial wait. Collapse the queue and
# lend the otherwise idle workers to the encoder itself.
if pending.length <= worker_count
  encoder_threads = worker_count
  worker_count = 1
end
unless pending.empty?
  worker_count = [worker_count, pending.length].min
  children = {}
  pending.each do |_sha256, (source, cached)|
    while children.length >= worker_count
      pid, status = Process.wait2
      summary[:encoder_failures] += 1 unless status.success?
      children.delete(pid)
    end

    pid = fork do
      # astcenc selects its output container from the filename extension. Keep
      # the temporary suffix before `.astc`, otherwise it rejects the output
      # as an unknown compressed-file type.
      temporary = "#{cached}.tmp-#{Process.pid}.astc"
      # Most of the bundle uses one thread per parallel image. The final
      # small queue uses the idle workers inside a single astcenc process.
      success = system(encoder, '-cl', source, temporary, '6x6', "-#{ASTC_PRESET}",
                       '-j', encoder_threads.to_s, '-silent')
      success &&= valid_astc?(temporary)
      if success
        FileUtils.mv(temporary, cached)
        exit 0
      end
      FileUtils.rm_f(temporary)
      warn "ASTC skipped #{source}"
      exit 1
    end
    children[pid] = source
  end
  until children.empty?
    pid, status = Process.wait2
    summary[:encoder_failures] += 1 unless status.success?
    children.delete(pid)
  end
end

entries.each do |source, sha256, cached|
  next unless valid_astc?(cached)

  original_bytes = File.size(source)
  astc_bytes = File.size(cached)
  next unless astc_bytes < original_bytes

  FileUtils.cp(cached, source, preserve: true)
  manifest << [sha256, original_bytes, astc_bytes, relative_to(source, data)].join("\t")
  summary[:converted] += 1
  summary[:saved_bytes] += original_bytes - astc_bytes
end

File.write(File.join(data, 'fluxara-ios-astc.tsv'), manifest.join("\n") + "\n")
puts "FLUXARA_IOS_ASTC converted=#{summary[:converted]} saved_bytes=#{summary[:saved_bytes]} encoder_failures=#{summary[:encoder_failures]} preset=#{ASTC_PRESET} cache=#{cache_dir}"
