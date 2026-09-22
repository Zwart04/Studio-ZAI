import 'package:flutter/material.dart';

import 'i18n/strings.dart';
import 'screens/clips_screen.dart';
import 'screens/home_screen.dart';
import 'screens/models_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/voice_screen.dart';
import 'state/app_state.dart';
import 'theme/tokens.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const StudioZaiApp());
}

class StudioZaiApp extends StatefulWidget {
  const StudioZaiApp({super.key});

  @override
  State<StudioZaiApp> createState() => _StudioZaiAppState();
}

class _StudioZaiAppState extends State<StudioZaiApp> {
  late final AppState _state;
  bool _ready = false;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _state = AppState(S('id'));
    _state.init().then((_) {
      if (mounted) setState(() => _ready = true);
    }).catchError((Object error) {
      if (mounted) setState(() => _error = error);
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Studio ZAI',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: _error != null
          ? _ErrorView(error: _error!)
          : (!_ready
              ? const Scaffold(body: Center(child: CircularProgressIndicator()))
              : ListenableBuilder(
                  listenable: _state,
                  builder: (context, _) => RootShell(state: _state),
                )),
    );
  }
}

class _LogoMark extends StatelessWidget {
  const _LogoMark({this.size = 76});

  final double size;

  @override
  Widget build(BuildContext context) {
    // Grayscale version of the brand logo so it blends with the dark UI.
    return ColorFiltered(
      colorFilter: const ColorFilter.matrix(<double>[
        0, 0, 0, 0, 255,
        0, 0, 0, 0, 255,
        0, 0, 0, 0, 255,
        0, 0, 0, 1, 0,
      ]),
      child: Image.asset('assets/images/logo.png', width: size, height: size, fit: BoxFit.contain),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error});

  final Object error;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(Tokens.space6),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const _LogoMark(size: 76),
              const SizedBox(height: Tokens.space3),
              const Icon(Icons.error_outline, color: Tokens.danger, size: 40),
              const SizedBox(height: Tokens.space3),
              const Text('Gagal memulai Studio ZAI'),
              const SizedBox(height: Tokens.space2),
              Text('$error', textAlign: TextAlign.center, style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
            ],
          ),
        ),
      ),
    );
  }
}

class RootShell extends StatefulWidget {
  const RootShell({super.key, required this.state});

  final AppState state;

  @override
  State<RootShell> createState() => _RootShellState();
}

class _RootShellState extends State<RootShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final pages = [
      HomeScreen(state: state, onOpenClips: () => setState(() => _index = 1)),
      ClipsScreen(state: state),
      VoiceScreen(state: state),
      ModelsScreen(state: state),
      SettingsScreen(state: state),
    ];

    return Scaffold(
      appBar: AppBar(
        leadingWidth: 52,
        leading: const Padding(
          padding: EdgeInsets.only(left: 12, top: 8, bottom: 8),
          child: _LogoMark(size: 32),
        ),
        title: const Text('Studio ZAI'),
        // Sedikit aksen merah di bawah app bar: palet utama tetap biru/abu,
        // merah hanya muncul sebagai penanda tipis (bukan memenuhi layar).
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(2),
          child: Container(
            height: 2,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Tokens.accent2, Colors.transparent],
                stops: [0.0, 0.3],
              ),
            ),
          ),
        ),
      ),
      body: SafeArea(child: IndexedStack(index: _index, children: pages)),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: [
          NavigationDestination(icon: const Icon(Icons.auto_awesome_motion), label: state.translate('nav.home')),
          NavigationDestination(icon: const Icon(Icons.movie_outlined), label: state.translate('nav.clips')),
          NavigationDestination(icon: const Icon(Icons.mic_none), label: state.translate('nav.voice')),
          NavigationDestination(icon: const Icon(Icons.memory), label: state.translate('nav.models')),
          NavigationDestination(icon: const Icon(Icons.settings_outlined), label: state.translate('nav.settings')),
        ],
      ),
    );
  }
}
