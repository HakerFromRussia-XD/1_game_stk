#!/usr/bin/env ruby
# frozen_string_literal: true

# Re-encodes iOS bundle audio to Opus after the curated Fluxara resources have
# been copied. Source tracks stay untouched: the generated bundle gets its own
# file names and its own XML references. Music keeps a higher bitrate because
# it is streamed; short effects use a smaller, still full-bandwidth setting.

require 'digest'
require 'fileutils'
require 'pathname'

abort "usage: #{$PROGRAM_NAME} <Fluxara Drift.app> <sox> <wav-to-opus> <cache-dir>" unless ARGV.length == 4

bundle, sox, encoder, cache_root = ARGV.map { |value| File.expand_path(value) }
data = File.join(bundle, 'data')
abort "missing app data: #{data}" unless Dir.exist?(data)
abort "missing SoX: #{sox}" unless File.executable?(sox)
abort "missing wav-to-opus encoder: #{encoder}" unless File.executable?(encoder)

MUSIC_BITRATE = ENV.fetch('FLUXARA_OPUS_MUSIC_KBPS', '96').to_i
SFX_BITRATE = ENV.fetch('FLUXARA_OPUS_SFX_KBPS', '48').to_i
AUDIO_PIPELINE_VERSION = 'sox-headroom-nodither-2'.freeze
abort 'Opus bitrates must be positive' unless MUSIC_BITRATE.positive? && SFX_BITRATE.positive?

TEXT_EXTENSIONS = %w[.xml .music .challenge .fluxara_driftgui].freeze

def valid_opus?(path)
  return false unless File.file?(path) && File.size(path) > 64

  header = File.binread(path, 128)
  header.start_with?('OggS') && header.include?('OpusHead')
end

def music_payloads(data)
  payloads = {}
  Dir.glob(File.join(data, '**', '*.music')).each do |music_file|
    File.binread(music_file).scan(/\b(?:file|fast-filename)\s*=\s*["']([^"']+\.ogg)["']/i) do |match|
      payloads[File.expand_path(File.join(File.dirname(music_file), match.first))] = true
    end
  end
  payloads
end

def relative_to(path, root)
  path.sub(/\A#{Regexp.escape(root)}\//, '')
end

def resolve_audio_path(reference, document, data, converted)
  candidates = [File.expand_path(File.join(File.dirname(document), reference))]
  candidates << File.expand_path(File.join(data, reference)) unless Pathname.new(reference).absolute?
  unless reference.include?('/')
    candidates << File.join(data, 'sfx', reference)
    candidates << File.join(data, 'music', reference)
  end
  candidates.find { |candidate| converted.key?(candidate) }
end

music = music_payloads(data)
entries = Dir.glob(File.join(data, '**', '*.ogg')).select { |path| File.file?(path) }.sort.map do |source|
  kind = music[File.expand_path(source)] ? 'music' : 'sfx'
  bitrate = kind == 'music' ? MUSIC_BITRATE : SFX_BITRATE
  digest = Digest::SHA256.file(source).hexdigest
  [source, digest, kind, bitrate]
end

cache_dir = File.join(cache_root, 'opus')
FileUtils.mkdir_p(cache_dir)
jobs = {}
entries.each do |source, digest, kind, bitrate|
  jobs[[digest, kind, bitrate]] ||= [source, File.join(cache_dir, "#{digest}-#{kind}-#{bitrate}-#{AUDIO_PIPELINE_VERSION}.opus"), bitrate]
end

pending = jobs.reject { |_key, value| valid_opus?(value[1]) }
workers = ENV.fetch('FLUXARA_OPUS_JOBS', '6').to_i
workers = 1 if workers < 1
failures = 0
unless pending.empty?
  workers = [workers, pending.length].min
  children = {}
  pending.each do |_key, value|
    source, cached, bitrate = value
    while children.length >= workers
      pid, status = Process.wait2
      failures += 1 unless status.success?
      children.delete(pid)
    end
    pid = fork do
      temporary = "#{cached}.tmp-#{Process.pid}.opus"
      wave = "#{cached}.tmp-#{Process.pid}.wav"
      # SoX supplies the high-quality Vorbis decode/resample.  The compact
      # local encoder then writes an Ogg/Opus stream without depending on a
      # mutable system ffmpeg installation.
      success = system(sox, '-G', '-D', source, '-r', '48000', '-b', '16', '-e',
                       'signed-integer', wave)
      success &&= system(encoder, wave, temporary, bitrate.to_s)
      success &&= valid_opus?(temporary)
      if success
        FileUtils.mv(temporary, cached)
        FileUtils.rm_f(wave)
        exit 0
      end
      FileUtils.rm_f(temporary)
      FileUtils.rm_f(wave)
      warn "Opus skipped #{source}"
      exit 1
    end
    children[pid] = source
  end
  until children.empty?
    pid, status = Process.wait2
    failures += 1 unless status.success?
    children.delete(pid)
  end
end

converted = {}
manifest = ["decision\toriginal_bytes\topus_bytes\tbitrate_kbps\tkind\tpath"]
saved_bytes = 0
retained = 0
entries.each do |source, digest, kind, bitrate|
  cached = jobs[[digest, kind, bitrate]][1]
  next unless valid_opus?(cached)

  original_bytes = File.size(source)
  opus_bytes = File.size(cached)
  # A few short effects can already be smaller in Vorbis.  Keep those exact
  # originals rather than replacing them with a larger lossy representation.
  if opus_bytes >= original_bytes
    retained += 1
    manifest << ['ogg', original_bytes, opus_bytes, bitrate, kind,
                 relative_to(source, data)].join("\t")
    next
  end

  target = source.sub(/\.ogg\z/i, '.opus')
  FileUtils.cp(cached, target, preserve: true)
  FileUtils.rm_f(source)
  converted[File.expand_path(source)] = target
  manifest << ['opus', original_bytes, opus_bytes, bitrate, kind,
               relative_to(source, data)].join("\t")
  saved_bytes += original_bytes - opus_bytes
end

Dir.glob(File.join(data, '**', '*')).each do |document|
  next unless File.file?(document) && TEXT_EXTENSIONS.include?(File.extname(document).downcase)

  contents = File.binread(document)
  rewritten = contents.gsub(/(["'])([^"']+\.ogg)\1/i) do |token|
    quote = Regexp.last_match(1)
    reference = Regexp.last_match(2)
    source = resolve_audio_path(reference, document, data, converted)
    source ? "#{quote}#{reference.sub(/\.ogg\z/i, '.opus')}#{quote}" : token
  end
  File.binwrite(document, rewritten) if rewritten != contents
end

File.write(File.join(data, 'fluxara-ios-opus.tsv'), manifest.join("\n") + "\n")
puts "FLUXARA_IOS_OPUS converted=#{converted.length} retained=#{retained} saved_bytes=#{saved_bytes} failures=#{failures} music_kbps=#{MUSIC_BITRATE} sfx_kbps=#{SFX_BITRATE} cache=#{cache_dir}"
