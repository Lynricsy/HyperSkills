// Part of package:shop_assets. Used by our build tooling on Windows, macOS and Linux.
import 'dart:convert';
import 'dart:io';

class AssetEntry {
  AssetEntry(this.name, this.hash);
  final String name;
  final String? hash; // optional in the manifest
}

class AssetManifest {
  AssetManifest(this.root, {required this.isDebug});

  final String root;
  final bool isDebug;

  List<AssetEntry> parse(String source) {
    final json = jsonDecode(source);
    final result = <AssetEntry>[];
    if (json is Map<String, dynamic> && json['entries'] is List) {
      for (final raw in json['entries'] as List) {
        // Manifest entries look like {"name": "assets/img/logo.png", "hash": "ab12"};
        // older generators omit "hash" entirely.
        if (raw case {'name': String name, 'hash': String? hash}) {
          result.add(AssetEntry(name, hash));
        }
      }
    }
    return result;
  }

  File fileFor(AssetEntry entry) => File('$root/${entry.name}');

  bool isBundled(String path) => path.startsWith('assets/');

  String bucketOf(String path) => path.split('/').skip(1).first;

  bool isImage(String path) => path.endsWith('.png') || path.endsWith('.jpg');

  /// Key written into the web manifest, which always uses forward slashes.
  String webKey(String nativePath) =>
      nativePath.substring(root.length + 1).replaceAll('\\', '/');

  String get label => switch (isDebug) {
        true => 'debug',
        false => 'release',
      };

  bool uploadSucceeded(int code) {
    if (code case >= 200 && < 300) {
      return true;
    }
    return false;
  }
}
