# HANDOFF

Terakhir ditulis: 2026-11-15 21:30 UTC. Kalau kamu (agent baru) membaca ini setelah
`/new`, **file ini satu-satunya sumber konteks.** Baca sampai habis sebelum menyentuh
apa pun. Jangan mengarang riwayat di luar yang tertulis di sini.

---

## 1. Tujuan

Ada dua pekerjaan terpisah.

**A. Submission Mogathon (utama, ada deadline).**
Deadline **19 Nov 2026**, pemenang diumumkan sebelum 20 Nov. Submission = posting di X
dan tag **@callmogbot**. Aturan resmi: kualitas di atas kuantitas, wajib ada judgment
sendiri, "AI is fine tapi one-click generation nggak cukup", Nobody seats tidak
stackable.

Produknya: **Motion Draft Room** — arena forecast di atas leaderboard kreator game
Motion, plus receipt book publik yang di-settle otomatis. Ide intinya: orang bikin
5 pick lineup + thesis + pre-mortem, pick-nya dikunci, lalu dinilai dari pergerakan rank
kreator pada snapshot berikutnya. Semua bisa dicek siapa pun.

**B. Batas context Hermes.**
`context_length: 112000` di `/data/home/.hermes/config.yaml` (endpoint menolak >128K).
Sudah beres, threshold kompaksi 84K. Jangan diutak-atik tanpa alasan.

---

## 2. Keputusan yang sudah diambil (jangan diulang pembahasannya)

**Sumber data hanya API resmi.** `https://leaderboard.motion.game/api/leaderboard`.
Tidak ada fallback pihak ketiga, tidak ada scraping. Snapshot pihak ketiga yang dulu
sempat masuk sudah dihapus dari repo.

**Collector tidak boleh jalan di VM ini.** VM ini standby tiap 30 menit, jadi apa pun
yang time-triggered harus hidup di luar: **GitHub Actions** cron `7 */4 * * *`
(00/04/08/12/16/20 UTC, mengikuti slot leaderboard Motion yang 4 jam).

**Satu snapshot per `(asOf, source)`.** Run ulang dalam window yang sama tidak menulis
file baru (print `[skip] already have ...`), tapi tetap me-refresh `data/latest.json`
supaya `asOf` tidak basi. Duplikat akan terbaca sebagai riwayat palsu di UI.

**Verifier menempel di workflow** dengan `if: always()`. Workflow hijau tidak
membuktikan slot terekam — hanya `collector/verify.py` yang bisa membedakan "sudah punya"
dari "cron tidak pernah jalan". Exit 0 semua ada / 1 ada gap / 2 source bukan resmi.
Ada opsi `--at` untuk simulasi.

**Skor dihitung server, bukan client.** `POST /api/receipts` menilai receipt dari
snapshot sendiri. Client tidak pernah mengirim skor. Satu receipt per handle per slot
(409 kalau duplikat) supaya orang tidak bisa re-roll.

**`_settle` idempoten.** Receipt yang sudah `status == "settled"` tidak dinilai ulang
dengan board hari ini.

**Identitas = X handle yang diketik user**, regex `^@?[A-Za-z0-9_]{1,15}$`, disimpan di
`localStorage['mdr_handle']`. Tanpa email, tanpa login. Handle invalid ditolak (400),
bukan disanitasi diam-diam.

**Rarity/boost dimodelkan sebagai asumsi yang dilabeli, bukan angka karangan.**
Docs resmi memberi formula `Lineup Score = Σ (Motion Score × Score Boost)`, memberi tahu
boost dari rarity, dan bahwa Legendary > Epic > Rare > Common. Yang **tidak**
dipublikasi: multiplier tiap tier, batas boost turnamen, cara boost digabung, dan Motion
Score itu sendiri. Jadi `engine/rarity.py` punya `DEFAULT_BOOST` sebagai satu konstanta
bernama yang ditandai `ASSUMED = True`, proyeksi memakai rank stand-in untuk Motion
Score, dan setiap angka dikembalikan bersama daftar asumsinya. **Rarity dicatat di
receipt tapi tidak pernah dipakai untuk menilai** — menilai dengan multiplier karangan
sendiri = skor palsu. Kalau Motion publish angka aslinya, ubah `DEFAULT_BOOST` di satu
tempat, engine + API + UI ikut.

**Kejujuran angka di UI itu fitur, bukan polish.** Contoh yang sudah dikerjakan: star
cost itu estimasi dari rank (bukan harga kartu asli); pips bintang dibuang karena 4
bintang terbaca 5, diganti `4/8`; header chip dan tile harus menyebut angka yang sama
(`3 snapshots in 2 windows`); receipt yang dikunci di window terbaru tampil "no window
yet" dan dikeluarkan dari penyebut hit-rate, bukan dihitung sebagai miss.

**Yang dilarang tanpa izin eksplisit user:** menghapus project Vercel `vprobe` beserta 2
alias-nya (item "nomor 5" di daftar lama). User bilang "lakuin semua kecuali nomor 5".
Jangan sentuh, jangan tanya ulang tiap sesi, tunggu user yang menyebut.

---

## 3. Status file

Repo lokal: `/data/workspace/motion-draft-room`. Remote
`https://github.com/frianowzki/motion-draft-room` (URL dengan token, jangan dicetak).
Branch aktif `main`, head **`ca35935`**. Branch `data` untuk snapshot + receipt.

Live: **https://motion-draft-room.vercel.app** — `/`, `/signals.json`, `/api/signals`,
`/api/receipts` (GET+POST) semua 200, sudah diverifikasi.

| File | Isi |
| --- | --- |
| `index.html` | UI satu halaman. `CAP=32, SIZE=5`, kolom star `${estStars}/8`, header `★ est`, empty card 4 langkah, `#stamp` "N snapshots in M windows", panel "Who is calling", panel "The book", pemilih rarity per pick, baris proyeksi `projected X · boosts ×Y · … not the game's Lineup Score`, `renderWho()`, `syncClear()`, `renderLineup()` tanpa arg |
| `engine/score.py` | `STAR_CAP=32`, `estStars` 1–8, `slotTimes` (window berbeda, bukan hitungan snapshot), blok `rarity` di output |
| `engine/rarity.py` | `DEFAULT_BOOST`, `ASSUMED`, `relative_strength()`, `project()`, `optimise()` (mengembalikan `feasible` + catatan bahwa batas boost belum terverifikasi) |
| `api/receipts.py` | GET semua receipt + `summary` (hitRate/pending/settled/netRank); POST validasi `HANDLE_RE`, cast `int(str(...))`, tulis `data/receipts.json` di branch `data` via GitHub API. Tanpa `GITHUB_TOKEN` POST ditolak dengan pesan jujur |
| `api/signals.py` | Sajikan `signals.json` |
| `collector/snapshot.py` | Dedupe `(asOf, source)`, jalur skip tetap refresh `latest.json` |
| `collector/verify.py` | Verifier slot; `SLOT_HOURS=4`, weekday-only, `--at` |
| `.github/workflows/collect.yml` | Cron `7 */4 * * *` + step "Verify the slot was recorded" (`if: always()`) |
| `data/game-rules.json` | Ringkasan docs resmi; rarity/boost pakai `null` eksplisit untuk angka yang tidak dipublikasi |
| `data/signals.json`, `data/latest.json`, `data/snapshots/` | Ada di kedua branch; snapshot resmi terakhir `asOf 2026-11-15T20:00:00Z`, `motion-official`, 79 rows |
| `data/receipts.json` | Hanya di branch `data`. **Sekarang kosong (`[]`)** — receipt tes sudah dibersihkan |
| `README.md` | Sumber angka, aturan resmi, alasan GitHub Actions, bagian rarity/boost, section Status (verified vs masih terbuka) |
| `build.sh`, `vercel.json`, `requirements.txt`, `.gitignore` | Build + konfigurasi deploy |

Kredensial ada di `/data/home/.hermes/.env` (`GITHUB_TOKEN`, `VERCEL_TOKEN`), nilainya
**jangan pernah dicetak**. `GITHUB_TOKEN` juga terpasang sebagai env production Vercel.
Selalu pipe output git/vercel lewat `grep -viE 'token'`.

Hal teknis yang pernah menggigit:
- `patch`/`write_file` menolak menulis `config.yaml` Hermes; edit lewat python + backup.
- Satu-satunya python yang punya `ruamel.yaml` ada di
  `/data/home/.hermes/installs/*/environments/*/venv/bin/python3`.
- `engine/score.py` di branch `data` pernah tertinggal dari `main` dan menghasilkan
  `signals.json` tanpa field baru. Kalau regenerate di branch `data`, pastikan
  `engine/` di-salin dari `main` dulu, lalu cek field-nya benar-benar ada.
- Bot Telegram ini jalan sebagai child dari `hermes-gateway.service`; restart lewat
  `/restart` di chat.

---

## 4. Next steps

Urut prioritas. Nomor 1 dan 2 adalah satu-satunya yang benar-benar menahan submission.

1. **Submit ke @callmogbot.** Belum dikerjakan dan tidak bisa dikerjakan agent — butuh
   akun X user. Deadline 19 Nov 2026. Posting harus memuat: apa produknya, link live,
   satu kalimat metodologi jujur (sumber API resmi, star estimasi, boost asumsi), dan
   sesuatu yang menunjukkan judgment manusia, bukan output satu klik.
2. **Tunggu run cron pertama yang benar-benar terjadwal.** Sejauh ini semua snapshot
   datang dari run manual di dalam slot yang sama, jadi `delta24h`/`delta72h` masih
   `null`. Setelah ada ≥3 window berbeda, angka itu terisi sendiri. Kalau run terjadwal
   gagal, `collector/verify.py` akan memerahkannya.
3. **Isi receipt book dengan call nyata.** Book sekarang kosong dan itu memang benar:
   receipt pertama harus call sungguhan, bukan data tes. Kalau menguji, pakai handle
   tes lalu **hapus lagi** dari branch `data` (lihat catatan di bawah).
4. **(Opsional, perlu izin user) hapus Vercel `vprobe` + 2 alias** — item "nomor 5"
   yang dikecualikan. Jangan jalan sendiri.
5. **(Opsional) redesign total UI.** User pernah bilang "ntar kita rombak total".
   Perbaikan sejauh ini bersifat rapikan/perbaiki, bukan rombak. Tunggu instruksi.

Catatan kerja yang berguna:
- Untuk menguji POST receipt di live lalu membersihkan: `git checkout data`,
  `git reset --hard origin/data`, buang receipt dengan `player` tes, commit, push.
  Branch `data` bisa telat beberapa detik setelah POST, jadi kalau `receipts.json`
  terbaca kosong padahal POST balas 201, tunggu dan fetch ulang — jangan menyimpulkan
  POST-nya gagal.
- Deploy: `vercel --prod --yes --token "$VERCEL_TOKEN"` dari
  `/data/workspace/motion-draft-room`, lalu verifikasi keempat endpoint dengan `curl`.
- Setelah mengubah `index.html`, cek sintaks: ambil isi `<script>` dan jalankan lewat
  `new Function(...)` di node.
- Jangan percaya screenshot sendirian untuk hal kecil; ukur lewat DOM (`getBoundingClientRect`,
  `getComputedStyle`) dan baru lihat gambar untuk kesan keseluruhan.

---

## 5. Hal yang tidak boleh diklaim

API resmi **tidak punya** handle X, tidak punya riwayat nyata (`history: "enabled"`
cuma string), dan tidak punya Motion Score kreator. Jangan pernah menulis di UI, README,
atau jawaban chat bahwa angka di sini sama dengan Motion Score / Lineup Score asli.
Tombol "submit" ke game tidak ada dan tidak akan ada — submission Mogathon adalah post
di X.
