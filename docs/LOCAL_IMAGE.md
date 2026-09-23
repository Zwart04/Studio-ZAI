# Gambar AI lokal

Studio ZAI menyediakan SDXS-512 untuk membuat gambar 512 × 512 di perangkat, tanpa akun, API key, atau server. Bobot model tidak dibundel dalam EXE/APK agar unduhan aplikasi tetap lebih kecil. Buka **Model → SDXS-512 → Unduh** satu kali; sesudah itu pembuatan gambar berjalan tanpa internet. Unduhan 682.847.200 byte diverifikasi dengan SHA-256 sebelum ditandai terpasang.

Model: [concedo/sdxs-512-tinySDdistilled-GGUF](https://huggingface.co/concedo/sdxs-512-tinySDdistilled-GGUF), turunan [IDKiro/sdxs-512-dreamshaper](https://huggingface.co/IDKiro/sdxs-512-dreamshaper), lisensi OpenRAIL++. Dokumentasi [stable-diffusion.cpp tentang model distilled](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/distilled_sd.md) menetapkan **1 langkah, CFG 1** untuk SDXS. File model yang dipakai: `sdxs-512-tinySDdistilled_Q8_0.gguf`, commit `3144d898d61492f8382ffcabec055733fc5b2a0e`, SHA-256 `409ab23582ee074c6b9d5395784fc0741b0599fb9d138686c69087c71678eb6a`.

Windows menyertakan paket CPU [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp/releases/tag/master-899-28b454b) resmi yang dipadatkan dalam `vendor/sd-cpp-win-cpu-28b454b.zip` (SHA-256 `cb55af2f5f112f5ef6a8b2785e25d44b5427714b89acae3f7c6fcf4ba7a72eb0`). Paket diekstrak di folder data aplikasi saat pertama kali dipakai. Lisensinya [MIT](licenses/stable-diffusion.cpp-MIT.txt).

APK arm64 menyertakan library CPU 16 KB-aligned dari [Local Diffusion](https://github.com/rmatif/Local-Diffusion) commit `184b7f92cf2f810e7d5eb4b04b190a5da829005f`, lisensi [Apache 2.0](licenses/local-diffusion-APACHE-2.0.txt). SHA-256 library: `4816ec18c4cd9683c186b0fe38333753c07b9a9db66b0e4125dfa7385d28d59e`. Bobot yang sama diunduh terpisah. Ponsel arm32 belum memiliki mesin gambar lokal. Kinerja dan kebutuhan RAM berbeda tiap perangkat; model 683 MB tetap membutuhkan RAM kerja tambahan.
Runtime `libomp.so` yang ikut APK berasal dari LLVM OpenMP, dengan [Apache 2.0 dan pengecualian LLVM](licenses/LLVM-Apache-2.0-Exception.txt). Berkas lisensi native juga ikut di aset APK.

Pilihan penyedia gambar online di Pengaturan tetap opsional. Jika dipilih, deskripsi gambar dikirim ke penyedia yang dikonfigurasi; mode lokal tidak mengirimkannya.
