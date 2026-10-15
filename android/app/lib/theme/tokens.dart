import 'package:flutter/material.dart';

/// Design tokens shared with the web UI (see ui/tokens.css) - CapCut-style dark.
///
/// Kebijakan warna: [accent]/[action] hanya untuk tombol utama, [red] untuk
/// tombol hapus. Tab aktif, seleksi, fokus, dan progress memakai netral.
class Tokens {
  static const bg = Color(0xFF141417);
  static const bgElevated = Color(0xFF1A1A1E);
  static const surface = Color(0xFF202024);
  static const surface2 = Color(0xFF2A2A2F);
  static const surface3 = Color(0xFF36363C);
  static const separator = Color(0x14FFFFFF);
  static const fill = Color(0x42787880);

  static const text = Color(0xFFF5F5F7);
  static const text2 = Color(0xFFE8E8ED);
  static const textDim = Color(0xFFA5A5AE);
  static const textDim2 = Color(0xFFA5A5AE);

  static const accent = Color(0xFF5AA9FF);
  static const action = Color(0xFF1F6FE0);
  static const accentPress = Color(0xFF1A5FC4);
  static const green = Color(0xFF34C759);
  static const orange = Color(0xFFFF9F0A);
  static const red = Color(0xFFFF8478);
  static const purple = Color(0xFFBF5AF2);

  // aliases kept for readability in screens
  static const success = green;
  static const warn = orange;
  static const danger = red;

  static const radiusSm = 10.0;
  static const radius = 14.0;
  static const radiusLg = 18.0;
  static const radiusPill = 999.0;

  static const space1 = 4.0;
  static const space2 = 8.0;
  static const space3 = 12.0;
  static const space4 = 16.0;
  static const space5 = 20.0;
  static const space6 = 24.0;
  static const space8 = 32.0;

  static const rowHeight = 48.0;
  static const motion = Duration(milliseconds: 220);
}

ThemeData buildTheme() {
  final base = ThemeData.dark(useMaterial3: true);

  return base.copyWith(
    scaffoldBackgroundColor: Tokens.bg,
    colorScheme: base.colorScheme.copyWith(
      primary: Tokens.accent,
      secondary: Tokens.accent,
      surface: Tokens.surface,
      onSurface: Tokens.text,
      error: Tokens.red,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Tokens.bg,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
      scrolledUnderElevation: 0,
      titleTextStyle: TextStyle(
        color: Tokens.text,
        fontSize: 20,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.4,
      ),
    ),
    cardTheme: CardThemeData(
      color: Tokens.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Tokens.radius)),
    ),
    listTileTheme: const ListTileThemeData(
      textColor: Tokens.text,
      iconColor: Tokens.textDim,
      contentPadding: EdgeInsets.symmetric(
          horizontal: Tokens.space4, vertical: Tokens.space1),
    ),
    dividerTheme:
        const DividerThemeData(color: Tokens.separator, thickness: 1, space: 1),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Tokens.surface2,
      hintStyle: const TextStyle(color: Tokens.textDim2),
      labelStyle: const TextStyle(color: Tokens.textDim, fontSize: 13),
      contentPadding: const EdgeInsets.symmetric(
          horizontal: Tokens.space3, vertical: Tokens.space3),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        borderSide: const BorderSide(color: Tokens.accent, width: 1.5),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Tokens.action,
        foregroundColor: Colors.white,
        minimumSize: const Size(0, 44),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(Tokens.radiusSm)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Tokens.text,
        backgroundColor: Tokens.fill,
        side: BorderSide.none,
        minimumSize: const Size(0, 44),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(Tokens.radiusSm)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: Tokens.accent,
        textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
      ),
    ),
    textTheme: base.textTheme
        .apply(bodyColor: Tokens.text, displayColor: Tokens.text)
        .copyWith(
          bodyLarge:
              const TextStyle(fontSize: 15, color: Tokens.text, height: 1.4),
          bodyMedium:
              const TextStyle(fontSize: 14, color: Tokens.text2, height: 1.4),
          bodySmall: const TextStyle(
              fontSize: 13, color: Tokens.textDim, height: 1.35),
          titleLarge: const TextStyle(
              fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.5),
          titleMedium: const TextStyle(
              fontSize: 17, fontWeight: FontWeight.w600, letterSpacing: -0.3),
        ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Tokens.bgElevated,
      elevation: 0,
      height: 58,
      indicatorColor: Colors.transparent,
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          size: 22,
          color: states.contains(WidgetState.selected)
              ? Tokens.accent
              : Tokens.textDim,
        ),
      ),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 11,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w600
              : FontWeight.w400,
          color: states.contains(WidgetState.selected)
              ? Tokens.accent
              : Tokens.textDim,
        ),
      ),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? Colors.white
            : const Color(0xFF8E8E93),
      ),
      trackColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? Tokens.green
            : Tokens.surface3,
      ),
    ),
    progressIndicatorTheme:
        const ProgressIndicatorThemeData(color: Tokens.accent),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: Tokens.surface2,
      contentTextStyle: const TextStyle(color: Tokens.text, fontSize: 14),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Tokens.radius)),
    ),
  );
}
