# ❄️ Prediksi Potensi Embun Beku Dieng

Aplikasi web (Streamlit) untuk memprediksi potensi embun beku di Dieng dari data AWS Batur.
Proyek magang BMKG Stasiun Klimatologi Semarang.

## Cara kerja singkat
1. Petugas **mengunggah file ekspor AWS (CSV/Excel) sekali tiap malam, setelah pukul 21.00 WIB**.
2. Sistem membersihkan data, menghitung titik embun (Magnus-Tetens), lalu model memprediksi
   apakah **dini hari besok (00.00-08.00 WIB)** suhunya ≤ 2°C (berpotensi embun beku).
3. Muncul banner/pop-up peringatan dan pesan siap salin untuk grup petani.
4. Halaman **Dashboard** menampilkan grafik 10 menit dan nilai puncak harian, mingguan, bulanan, tahunan.

Dua lapis peringatan:
- **Prediksi (model ML):** besok dini hari berpotensi atau tidak, dengan tingkat Waspada/Siaga/Awas dari skor model.
- **Pemantauan langsung (aturan jurnal ELKOMIKA 2024):** suhu ≤ 2°C = Waspada, + angin ≤ 5 m/s = Siaga, + RH ≥ 60% = Awas.

## Format file unggahan
Kolom wajib: `Tanggal`, `tt_air_avg` (suhu), `rh_avg` (kelembapan), `ws_avg` (angin).
Opsional: `sr_avg`, `wd_avg`, `rr`. Satu baris = satu pengamatan 10 menit.
Kolom `Tanggal` berformat UTC seperti ekspor AWS (`2023-08-09 17:00:00+00`); pilih "WIB" di aplikasi bila sudah WIB.

## Catatan
- Hasil adalah alat bantu, **bukan peringatan resmi BMKG**.
