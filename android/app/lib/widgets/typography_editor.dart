import 'package:flutter/material.dart';
import '../state/app_state.dart';

Future<String?> editTypography(BuildContext context, AppState state) async {
  final name = TextEditingController(text: 'Gaya saya');
  final color = TextEditingController(text: '#FFFFFF');
  final outline = TextEditingController(text: '#000000');
  var font = 'Anton';
  var size = 64.0;
  var box = false;
  String? error;
  final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
          builder: (context, update) => AlertDialog(
                title: const Text('Template buatanmu'),
                content: SizedBox(
                    width: 400,
                    child: SingleChildScrollView(
                        child:
                            Column(mainAxisSize: MainAxisSize.min, children: [
                      TextField(
                          controller: name,
                          maxLength: 48,
                          decoration: const InputDecoration(
                              labelText: 'Nama template')),
                      DropdownButtonFormField<String>(
                          initialValue: font,
                          items: [
                            'Inter',
                            'Anton',
                            'Barlow Condensed',
                            'DM Serif Display',
                            'Kalam'
                          ]
                              .map((f) =>
                                  DropdownMenuItem(value: f, child: Text(f)))
                              .toList(),
                          onChanged: (v) => update(() => font = v!),
                          decoration: const InputDecoration(labelText: 'Font')),
                      TextFormField(
                          initialValue: '64',
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Ukuran relatif (24–144)'),
                          onChanged: (v) => size = double.tryParse(v) ?? 64),
                      TextField(
                          controller: color,
                          decoration: const InputDecoration(
                              labelText: 'Warna teks · #RRGGBB')),
                      TextField(
                          controller: outline,
                          decoration: const InputDecoration(
                              labelText: 'Warna tepi / kotak · #RRGGBB')),
                      SwitchListTile(
                          title: const Text('Latar kotak'),
                          value: box,
                          onChanged: (v) => update(() => box = v)),
                      if (error != null) Text(error!),
                    ]))),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(dialogContext),
                      child: const Text('Batal')),
                  FilledButton(
                      onPressed: () async {
                        if (!RegExp(r'^#[0-9a-fA-F]{6}$')
                                .hasMatch(color.text) ||
                            !RegExp(r'^#[0-9a-fA-F]{6}$')
                                .hasMatch(outline.text)) {
                          update(() => error =
                              'Gunakan warna #RRGGBB, misalnya #FFFFFF.');
                          return;
                        }
                        String ass(String hex) =>
                            '&H00${hex.substring(5, 7)}${hex.substring(3, 5)}${hex.substring(1, 3)}';
                        final id = await state.saveTypography({
                          'label': name.text.trim().isEmpty
                              ? 'Gaya saya'
                              : name.text.trim(),
                          'font': font,
                          'size': size.clamp(24, 144),
                          'primary': ass(color.text),
                          'secondary': ass(color.text),
                          'outlineColour': ass(outline.text),
                          'outline': 3,
                          'shadow': 1,
                          'bold': -1,
                          'border': box ? 3 : 1,
                          'karaoke': false,
                          'anim': '',
                          'marginV': 220,
                          'previewColor': color.text,
                          'previewOutline': outline.text,
                          'category': 'Custom',
                          'sample': 'Your words. Your style.'
                        });
                        if (dialogContext.mounted) {
                          Navigator.pop(dialogContext, id);
                        }
                      },
                      child: const Text('Simpan'))
                ],
              )));
  await Future<void>.delayed(const Duration(milliseconds: 250));
  name.dispose();
  color.dispose();
  outline.dispose();
  return result;
}
