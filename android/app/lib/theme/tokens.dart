import 'package:flutter/material.dart';

/// Design tokens shared with the web UI (see ui/tokens.css).
class Tokens {
  static const bg = Color(0xFF0B0E14);
  static const surface = Color(0xFF141824);
  static const surface2 = Color(0xFF1C2230);
  static const border = Color(0xFF252C3B);
  static const text = Color(0xFFE8EAF0);
  static const textDim = Color(0xFF9AA3B5);
  static const accent = Color(0xFF6C5CE7);
  static const accentPress = Color(0xFF5A4BD1);
  static const success = Color(0xFF2ECC71);
  static const warn = Color(0xFFF1C40F);
  static const danger = Color(0xFFE74C3C);

  static const radiusSm = 8.0;
  static const radius = 12.0;
  static const radiusPill = 999.0;

  static const space1 = 4.0;
  static const space2 = 8.0;
  static const space3 = 12.0;
  static const space4 = 16.0;
  static const space6 = 24.0;
  static const space8 = 32.0;

  static const motion = Duration(milliseconds: 150);
}

ThemeData buildTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: Tokens.bg,
    colorScheme: base.colorScheme.copyWith(
      primary: Tokens.accent,
      surface: Tokens.surface,
      onSurface: Tokens.text,
      error: Tokens.danger,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Tokens.bg,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        color: Tokens.text,
        fontSize: 20,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.2,
      ),
    ),
    cardTheme: CardTheme(
      color: Tokens.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(Tokens.radius),
        side: const BorderSide(color: Tokens.border),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Tokens.surface2,
      contentPadding: const EdgeInsets.all(Tokens.space3),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        borderSide: const BorderSide(color: Tokens.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        borderSide: const BorderSide(color: Tokens.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        borderSide: const BorderSide(color: Tokens.accent),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Tokens.accent,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: Tokens.space4, vertical: Tokens.space3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Tokens.radiusSm)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Tokens.text,
        side: const BorderSide(color: Tokens.border),
        padding: const EdgeInsets.symmetric(horizontal: Tokens.space4, vertical: Tokens.space3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Tokens.radiusSm)),
      ),
    ),
    textTheme: base.textTheme.apply(bodyColor: Tokens.text, displayColor: Tokens.text),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Tokens.surface,
      indicatorColor: Tokens.accent.withValues(alpha: 0.16),
      labelTextStyle: WidgetStateProperty.all(
        const TextStyle(fontSize: 12, color: Tokens.textDim),
      ),
    ),
    dividerTheme: const DividerThemeData(color: Tokens.border, space: 1),
  );
}
