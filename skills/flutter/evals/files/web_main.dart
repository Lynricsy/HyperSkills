import 'package:flutter/material.dart';

import 'src/app_router.dart';
import 'src/theme.dart';

// Entry point for the customer-facing web storefront (flutter build web).
// The same widgets ship in the iOS and Android apps, where TalkBack and
// VoiceOver read every button and product card correctly.
void main() {
  runApp(const StorefrontApp());
}

class StorefrontApp extends StatelessWidget {
  const StorefrontApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Storefront',
      theme: storefrontTheme,
      routerConfig: appRouter,
    );
  }
}
