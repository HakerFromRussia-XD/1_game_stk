#!/usr/bin/env ruby
# Runtime textures exported for reusable track libraries.
# The Blender source library and its historical variants are stored elsewhere.
require 'digest'
require 'fileutils'
abort 'usage: CopyFluxaraSharedTrackTextures.rb <runtime-source-textures> <bundle-textures>' unless ARGV.length == 2
source, destination = ARGV.map { |p| File.expand_path(p) }
abort "missing source directory: #{source}" unless Dir.exist?(source)
abort "missing bundle texture directory: #{destination}" unless Dir.exist?(destination)
count = 0
bytes = 0
Dir.children(source).sort.each do |name|
  path = File.join(source, name)
  next unless File.file?(path)
  next unless /\.(?:png|jpe?g|dds|astc)\z/i.match?(name)
  match = /\Afluxara_pool_([0-9a-f]{12})\.(?:png|jpg|jpeg)\z/.match(name)
  if name.start_with?('fluxara_pool_') && !match
    abort "unexpected shared texture filename: #{name}"
  end
  sha = Digest::SHA256.file(path).hexdigest
  abort "shared texture hash mismatch: #{name}" if match && !sha.start_with?(match[1])
  target = File.join(destination, name)
  # Named Fluxara overlays supersede generated baseline pixels. SHA-named
  # assets stay immutable and must never collide with different bytes.
  if File.exist?(target) && match && Digest::SHA256.file(target).hexdigest != sha
    abort "conflicting shared texture: #{name}"
  end
  if !File.exist?(target) || Digest::SHA256.file(target).hexdigest != sha
    FileUtils.cp(path, target, preserve: true)
  end
  count += 1
  bytes += File.size(path)
end
puts "Fluxara shared track textures: #{count} files, #{bytes} bytes"
