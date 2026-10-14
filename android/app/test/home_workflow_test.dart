import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/i18n/strings.dart';
import 'package:studiozai/screens/home_screen.dart';
import 'package:studiozai/state/app_state.dart';

void main() {
  testWidgets('Transcript task hides moment controls without changing source',
      (tester) async {
    final state = AppState(S('id'));
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(body: HomeScreen(state: state, onOpenClips: () {}))));
    expect(find.text('Hybrid Local AI'), findsNothing);
    await tester.ensureVisible(find.byType(DropdownButtonFormField<bool>));
    await tester.tap(find.byType(DropdownButtonFormField<bool>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Transkrip saja').last);
    await tester.pumpAndSettle();
    expect(find.text('Deteksi momen'), findsNothing);
    expect(find.text('Hasil klip'), findsNothing);
    await tester.ensureVisible(find.text('Buat transkrip'));
    expect(find.text('Buat transkrip'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('Canvas choices fit a narrow phone', (tester) async {
    tester.view.physicalSize = const Size(320, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: HomeScreen(state: AppState(S('id')), onOpenClips: () {}))));
    await tester.scrollUntilVisible(find.text('16:9 Landscape'), 350,
        scrollable: find.byType(Scrollable).first);
    await Scrollable.ensureVisible(tester.element(find.text('16:9 Landscape')),
        alignment: 0.5);
    await tester.pumpAndSettle();
    await tester.tap(find.text('16:9 Landscape'));
    await tester.pumpAndSettle();
    expect(
        tester
            .widget<ChoiceChip>(find.ancestor(
                of: find.text('16:9 Landscape'),
                matching: find.byType(ChoiceChip)))
            .selected,
        isTrue);
    expect(tester.takeException(), isNull);
  });
}
