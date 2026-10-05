#!/usr/bin/env ruby
# Verify that every legacy texture name embedded in bundled SPM meshes has a
# corresponding renamed image. Runtime resolves the alias in FileManager.
require 'rexml/document'

data = File.join(ARGV.fetch(0), 'data')
abort "missing bundle data: #{data}" unless Dir.exist?(data)

images = Dir.glob(File.join(data, '**', '*.{png,jpg,jpeg}'))
            .each_with_object({}) { |path, index| index[File.basename(path)] = true }
missing = {}
checked = 0
Dir.glob(File.join(data, '**', '*.spm')).each do |mesh|
  File.binread(mesh).scan(/stk[A-Za-z0-9_\-]*\.(?:png|jpe?g)/i).uniq.each do |legacy|
    checked += 1
    next if images[legacy]
    renamed = legacy.sub(/\Astk/, 'fluxara_drift')
                    .sub('stkVertical', 'fluxara_driftVertical')
    missing[legacy] ||= mesh unless images[renamed]
  end
end

missing.sort.each do |name, mesh|
  warn "unresolved SPM texture #{name} in #{mesh}"
end
abort "#{missing.length} unresolved legacy SPM textures" unless missing.empty?
puts "FLUXARA_IOS_SPM_TEXTURES_RESOLVED references=#{checked}"

# Kart material declarations are loaded even when their meshes do not use the
# named texture. Reject stale declarations so the runtime log stays actionable.
shared = Dir.glob(File.join(data, '{textures,models}', '**', '*.{png,jpg,jpeg}'))
            .each_with_object({}) { |path, index| index[File.basename(path)] = true }
bad_materials = []
Dir.glob(File.join(data, 'karts', '*', 'materials.xml')).each do |xml|
  local = Dir.glob(File.join(File.dirname(xml), '*.{png,jpg,jpeg}'))
             .each_with_object({}) { |path, index| index[File.basename(path)] = true }
  REXML::Document.new(File.read(xml)).elements.each('materials/material') do |material|
    %w[name gloss-map normal-map].each do |attribute|
      name = material.attributes[attribute]
      next if name.nil? || name.empty? || local[name] || shared[name]
      bad_materials << "#{xml}: #{attribute}=#{name}"
    end
  end
end
bad_materials.each { |error| warn "unresolved kart material #{error}" }
abort "#{bad_materials.length} unresolved kart materials" unless bad_materials.empty?
puts 'FLUXARA_IOS_KART_MATERIALS_RESOLVED'
