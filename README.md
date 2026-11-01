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

## Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```
Butuh Python 3.11 atau lebih baru (karena `scikit-learn==1.8.0`).

Untuk menjalankan notebook `Pipeline_Embun_Beku.ipynb`, pasang dependensi dari folder
`embun_beku_app` dengan perintah yang sama, lalu pilih interpreter Python tersebut sebagai
kernel notebook di VS Code. Ini memastikan `joblib`, `scikit-learn`, dan dependensi notebook
lainnya tersedia di kernel yang digunakan.

Model di folder `model/` dibuat dengan scikit-learn 1.8.0. Kalau versi di komputermu berbeda dan muncul error saat
memuat model, jalankan ulang notebook `Pipeline_Embun_Beku.ipynb`, lalu salin `model_embun_beku.joblib`,
`info_model.json`, dan `data_bersih_10menit.csv.gz` hasilnya ke folder `model/` dan `data/`.

## Struktur
```
app.py                  pintu masuk + navigasi
core/pipeline.py        cleaning, fitur, label, agregasi (SAMA dengan notebook)
core/model.py, data.py  muat model/data, proses file unggahan
components/             sidebar, grafik Plotly, notifikasi
views/                  Beranda, Prediksi, Dashboard, Metodologi
model/                  model_embun_beku.joblib, info_model.json
data/                   data_bersih_10menit.csv.gz (data historis 2021-2025)
contoh/                 dua file contoh untuk mencoba unggah
```

## Format file unggahan
Kolom wajib: `Tanggal`, `tt_air_avg` (suhu), `rh_avg` (kelembapan), `ws_avg` (angin).
Opsional: `sr_avg`, `wd_avg`, `rr`. Satu baris = satu pengamatan 10 menit.
Kolom `Tanggal` berformat UTC seperti ekspor AWS (`2023-08-09 17:00:00+00`); pilih "WIB" di aplikasi bila sudah WIB.

## Catatan
- Kalau mengubah aturan di notebook (ambang, jam jendela), ubah juga di `core/pipeline.py`.
- Hasil adalah alat bantu, **bukan peringatan resmi BMKG**.
