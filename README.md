# ROXYU SIM — Paper Trading + Telegram

Proyek demo belajar yang terinspirasi dari gaya dashboard pada video, bukan salinan kode/layanan asli.
Semua transaksi adalah **simulasi dengan saldo virtual $10.000**. Tidak ada exchange atau uang sungguhan yang dihubungkan.

## Isi
- `app.py`: dashboard web + Telegram bot polling.
- `requirements.txt`: dependensi.
- `render.yaml`: template deploy di Render.

## Cara paling mudah dari HP Android
1. Buka `https://t.me/BotFather` di Telegram.
2. Kirim `/newbot`, ikuti instruksi, lalu salin token bot. **Jangan bagikan token ini kepada siapa pun.**
3. Di browser HP, masuk ke `https://render.com` dan buat akun.
4. Buat repository GitHub baru di `https://github.com/new`. Upload `app.py`, `requirements.txt`, dan `render.yaml` dari ZIP ini (bisa melalui browser HP).
5. Di Render, pilih **New + → Blueprint**, hubungkan repository tadi, lalu deploy.
   - Jika Blueprint tidak tersedia, pilih **New + → Web Service**, hubungkan repo, Build Command: `pip install -r requirements.txt`, Start Command: `python app.py`.
6. Di pengaturan Environment service, tambahkan:
   - `BOT_TOKEN` = token dari BotFather
   - `PUBLIC_URL` = URL HTTPS service Render, misalnya `https://nama-service.onrender.com`
7. Deploy/redeploy, lalu buka bot Telegram dan kirim `/start`.
8. Buka URL Render untuk dashboard.

> Layanan gratis dapat tidur saat tidak digunakan, dan penyimpanan lokal/memori bisa hilang ketika service restart. Ini cocok untuk demo, bukan pencatatan keuangan atau layanan trading produksi. Periksa kebijakan/biaya terbaru platform hosting.

## Perintah Telegram
- `/start` atau `/help`
- `/status`
- `/prices` — harga acak simulasi, bukan harga pasar live
- `/positions`
- `/buy BTC 250` — beli BTC senilai $250 virtual
- `/sell BTC` — tutup semua posisi BTC
- `/reset` — kembali ke saldo $10.000 virtual
- `/dashboard`

Aset simulasi: BTC, ETH, SOL. Dashboard dan bot berbagi state selama satu proses server aktif.

## Catatan keamanan
- Jangan pernah memasukkan token bot ke kode publik atau mengirimkannya di chat.
- Jika token terlanjur bocor, buat token baru lewat BotFather dengan `/revoke`.
- Jangan masukkan API key exchange. Proyek ini tidak membutuhkan API key exchange.
- Dashboard demo tidak memakai login; jangan simpan informasi pribadi atau menggunakannya untuk data sensitif.
