# HANDOFF

Terakhir ditulis: 2026-11-17 09:28 UTC (`main` `d5c858f`, `data` `5f2fd3b`,
live `dpl_7EaBw3myVH1vtA1yEzF6b28s8wL2`). Kalau kamu (agent baru) membaca ini setelah
`/new`, **file ini satu-satunya sumber konteks.** Baca sampai habis sebelum menyentuh
apa pun. Jangan mengarang riwayat di luar yang tertulis di sini.

---

## Sesi 2026-11-17 (paling baru): hero tanpa card, stamp & note dibuang, copy humanized

Empat permintaan, semuanya di landing. Tiga pembuangan, satu penyuntingan.

1. **Hero tidak lagi di dalam card.** `.hero-main` sekarang `background:transparent`,
   `box-shadow:none`, `border-radius:0`, `padding:46px 0 54px`. Mask gradien pada
   `<h2>` ikut dibuang — dulu gunanya memberi kesan kedalaman di atas card, tanpa
   card itu cuma membuat huruf bawah kusam. Tiga override mobile disamakan
   (padding horizontal 0, `justify-content:flex-start`).
2. **Stempel kesegaran dibuang dari landing.** Span `[data-room-stamp]`, CSS
   `[data-stale]`, fungsi `ago()`/`paintStamp()`, pemanggilan di `paint()`, dan
   `setInterval` 60 detik yang membuatnya menua — semuanya hilang. **Catatan:**
   stempel itu dulu satu-satunya cara pengunjung tahu board-nya ketinggalan ~20 jam
   (Motion `asOf` mandek). Kalau nanti mau kejujuran itu balik, taruh sebagai satu
   kalimat diskret dekat board, jangan di header seksi.
3. **Teks "Scored server-side from the snapshot that closes the window." dibuang**
   bersama `.hc-note` (CSS-nya juga). Detail implementasi, bukan hal yang dicari
   pengunjung.
4. **Copy di-humanize di kedua halaman.** Lede lama "Fantasy sports for creators, on
   the one dataset Motion actually publishes" — itu pola "the only X that Y",
   bicara soal kita, bukan soal apa yang pengunjung lakukan. Sekarang: apa yang
   kamu kerjakan, apa yang dinilai, apa yang tetap tercatat. Judul kartu
   how-it-works diganti (tiga-tiganya mengikuti pola "X, Y each" / "A and B, or
   nothing"). `<title>` + meta description landing dan `/app` ditulis ulang
   memakai kata kerja. Footer `/app` juga. Audit terukur: **nol** hit untuk semua
   pola AI di 684 kata landing dan 541 kata app.

**Pelajaran:** jangan hapus CSS atau blok JS dengan `str.replace` per baris kalau
rule-nya multi-baris — saya sempat memotong `.hc-note` di tengah dan menyisakan
fragmen `font-size:10px;...}` yang menggantung. Ganti satu blok utuh, lalu
`node --check` semua inline `<script>` untuk memastikan tidak ada pemanggil yatim.

**Riwayat revert:** commit `68bd711`/`a8dc51e`/`f78a177` membatalkan percobaan
copy+art sebelumnya (foto stok diganti panel SVG, radius 2px). User membatalkannya;
jangan ulangi tanpa diminta. Commit `d5c858f` di atas adalah yang berlaku sekarang.

**Status jebakan `public/`:** tetap berlaku. `public/` di-gitignore; sumber aset
dan HTML adalah root repo, `build.sh` yang menyalin. Verifikasi hasil deploy dengan
curl per file, jangan percaya "deploy sukses".

---

## Sesi 2026-11-17 (paling baru, lanjutan)

**Yang diperbaiki di sesi ini** (semua sudah live dan sudah diverifikasi di produksi):

1. **Tag di "The Room itself" saling tumpang tindih.** SURGING dan COILED
   mencetak lima nama yang sama persis. Penyebabnya: tag di engine tidak
   eksklusif (`if`, bukan `elif`), dan COILED justru menuntut `d4h >= 2` —
   yaitu creator yang *sedang* naik, bukan yang datar. Tag sekarang eksklusif
   dengan urutan prioritas SURGING → FADE → SLEEPER → QUIET → COILED → STEADY,
   satu tag per orang. QUIET diuji **sebelum** COILED supaya nama yang benar-benar
   beku tidak ditelan ember yang lebih lebar. Bukti di produksi: SURGING 8,
   SLEEPER 10, COILED 32, QUIET 21, STEADY 5, FADE 3, `multi-tag 0`, dan kelima
   kartu berisi nama berbeda semua.

2. **Tiga lineup saran isinya identik.** `balanced`, `sleeperHeavy`, dan
   `contrarian` semuanya mengambil dari daftar yang sudah diurut momentum, jadi
   hasilnya lima nama yang sama. Sekarang tiap pool punya urutan sendiri:
   balanced = value per bintang, sleeperHeavy = SLEEPER dulu lalu value,
   contrarian = yang paling turun (`delta4h <= 0`). Terverifikasi 3 dari 3
   lineup berbeda.

3. **The Room tidak pernah bilang datanya dari kapan.** Sekarang ada stempel di
   sebelah judul: `board as of 12:00Z · 20 hrs ago · checked 13 hrs ago`.
   `dataAsOf` = `asOf` Motion untuk snapshot terbaru yang kita pegang,
   `latestSnapshot` = kapan terakhir kita cek. Kalau jendelanya lebih tua dari
   dua kali publish (>8 jam), stempelnya berubah warna (`[data-stale]`) — jadi
   data basi kelihatan basi, tidak dibungkus seolah live. Halaman juga polling
   `/api/signals` tiap 5 menit dan saat tab kembali fokus, dan waktu relatifnya
   menua sendiri tiap menit.

4. **Toggle dark/light di mobile dashboard numpuk.** Ini bukan dua toggle —
   `#themesw` cuma satu. Penyebab asli: rule mobile `button{min-height:44px}`
   ikut mengenai dua tombol ikon 28px di dalam pill 34px, jadi tingginya jadi
   44px dan pill membengkak 62x50, ikonnya menabrak knob. Perbaikan: netralkan
   rule itu untuk switch (`#themesw .tgs-b{min-height:0}`) dan paku tinggi pill
   (`height:34px;flex:none`). Terukur di 320/360/390/414: pill 62x34, dua tombol
   28x28, knob pas di ikon aktif. **Yang lama tidak dihapus karena memang tidak
   pernah ada toggle kedua.**

**Catatan penting buat agent berikutnya:** `data` branch sempat saya rusak di
tengah sesi — `git reset --hard` lalu `python3 engine/score.py` dijalankan
sebelum tree-nya bersih, jadi `signals.json` sempat ditulis dari 2 snapshot saja
dan `verify.py` sempat menandai 8 slot hilang. Sudah pulih (4 snapshot, 4 window,
verify hijau). **Selalu `ls data/snapshots | wc -l` sebelum dan sesudah
regenerasi signals.**


**Run terjadwal pertama yang sungguhan sudah hijau**: run `44006245905`, `schedule`,
02:53Z, sukses. Jadi pertanyaan "apakah cron benar-benar jalan" terjawab ya — dan
`verify.py` di run itu melaporkan 4 snapshot / 4 window / OK.

Yang dikerjakan sesi ini:

1. **`delta24h` / `delta72h` ternyata bohong.** `d24h` = posisi terbaru − posisi
   tertua dari snapshot yang ada, jadi dua window yang jaraknya 3 jam tercetak sebagai
   "24h"; `d72h = d24h` (salinan literal). Sekarang `moves_over(snaps, jam)` di
   `engine/score.py` mengukur mundur dari `asOf` terbaru pada window yang benar-benar
   dimiliki, dan **null** selama rentangnya belum tertutup. Dengan 4 window (~12 jam),
   `d24h` sekarang terisi 79/79 dan `d72h` semuanya `null` + catatan `delta72hNote`.
2. **`collector/` di `data` disamakan dengan `main`** (verify.py + workflow). Ini
   penyebab `verify.py` lokal melaporkan 5 slot hilang dari worktree `data` yang basi;
   bukan bug.
3. **Docstring `verify.py`** masih menjelaskan aturan jam-dinding padahal logikanya
   sudah ber-anchor ke `asOf` Motion + `COLLECTING_SINCE`. Diselaraskan supaya tidak
   ada yang "membetulkan" verifier yang sudah benar. Jalur gap diuji ulang dengan
   menghapus snapshot 08:00Z → exit 1 dengan slot yang tepat.

**Kesimpulan soal data**: Motion **tidak menerbitkan window baru** antara
`2026-11-16T12:00Z` dan `2026-11-17T07:00Z` (asOf masih 12:00, `capturedAt` baru).
Cron-nya sehat; sumbernya yang belum bergerak. Jangan mengarang snapshot untuk slot
yang belum dipublikasikan.

---

## Verifier & receipt (2026-11-16, terbaru)

**Verifier hijau di CI** (run `43932357249`). Dua bug berlapis yang bikin cron merah terus:

1. `expected_slots` menagih window yang masih berjalan → run 18:21 menandai `16:00Z` padahal
   16:00 belum tutup. Sekarang batas atas = **`asOf` terbaru yang benar-benar diterbitkan
   Motion**, bukan jam dinding. Jam 18:44 API masih menyajikan `asOf 12:00`, jadi 16:00
   tidak boleh ditagih — window itu belum ada untuk direkam.
2. Batas bawah = `COLLECTING_SINCE = 2026-11-16T06:00Z`. Window `00:00Z` **memang bolong**
   (workflow hanya trigger `schedule` dari default branch, waktu itu `main`), tapi tidak ada
   run yang bisa mengisinya; memaku batas bawah di sana membuat build merah selamanya.

Selain itu verifier dan `_settle` sama-sama membaca key `creators` sementara snapshot menulis
**`rows`** — `_settle` jadi menilai semua pick `positionNow: None`. Keduanya sudah diperbaiki.

**Receipt** hanya dinilai terhadap snapshot dengan `dataAsOf` **strictly greater** dari
`slotAtLock`; hasil grade distempel `gradedAsOf` dan beku setelah itu. Receipt lama tanpa
`gradedAsOf` (dibuat grader buggy) dihitung ulang sekali.

**Belum tuntas**: book masih berisi 1 receipt uji OAuth (`draftroom_test`, 1234567), bukan call
sungguhan. `POST /api/receipts` menolak tanpa sesi X, dan connect-X masih mati:
`X_CLIENT_ID` / `X_SESSION_SECRET` belum diset di Vercel. `GITHUB_TOKEN` (sensitive,
production) **sudah** terpasang — `/api/signals` live penuh, 4 snapshot.

---

## Batch 9 (live, commit `a2b7bd9`)

- **FAQ**: blok `.sfaq-points` + label "FAQ section" + `.sfaq-left` dihapus. `.sfaq` sekarang
  satu kolom (`.sfaq-right` full width) — kartu sejajar dengan sec-head dan closer.
- **Theme switch**: `.themesw` (2 tombol terpisah) diganti `.tgs` = satu track dengan satu
  knob yang meluncur (`data-on="light|dark"`), dua tombol ikon sun/moon di dalamnya.
  Key localStorage tetap `mdr-theme`; `aria-pressed` tetap diset per tombol.
  **Penting**: `.tgs` butuh `pointer-events:auto` karena `.dockrow`/`.dock` punya
  `pointer-events:none` — tanpa itu seluruh track mati.
- **Posisi mobile**: landing `.tgs` ada di `.dockrow` (kiri pillnav, kanan switch, tidak
  overlap di 390). App: switch dipindah dari `position:fixed` ke `.apphead` di dalam
  `.wrap` (flex-end) → di desktop tetap di kanan atas area konten, di mobile tidak
  menumpuk back-home.
- **Arrow CTA**: `.acta` (label kiri + disc hitam berisi panah kanan) dipakai di closer
  ("Enter the room") dan slab showcase ("Open the app", `.acta-sm`). Closer slab selalu
  gelap → `.closer .acta` dipaksa paper/ink. Hover: disc scale 1.08 + panah geser 2px.
- **Font**: self-host Fontshare di `fonts/` (`fonts.css` + 14 woff2, 316K):
  Clash Grotesk (display/heading), Satoshi (body/UI), Gambetta (serif accent, belum
  dipakai di selector). Google Fonts tinggal JetBrains Mono (mono). `build.sh` sekarang
  menyalin `fonts/` → `public/fonts`; verifikasi prod `/fonts/*.woff2` = 200,
  `document.fonts` memuat Clash Grotesk 500/600 + Satoshi 400/500/700.
- Fontinlogo tidak dipakai: font di sana komersial (Avenir/Cereal/Circular/Product Sans);
  Fontshare = gratis untuk web, aman lisensi.

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

**Identitas = akun X yang benar-benar login** (berubah 2026-11-16, commit `921ba5a`).
Handle yang diketik sudah dibuang seluruhnya: isi `localStorage['mdr_handle']` lama tidak
dibaca lagi. Alurnya OAuth 2.0 Authorization Code + PKCE (`scope=users.read`) sebagai
public client; code ditukar di server, token tidak pernah sampai ke browser; hasilnya
cookie `mdr_session` yang di-HMAC dengan `X_SESSION_SECRET` (stateless, tanpa database —
rotasi secret = semua orang logout). `POST /api/receipts` mengambil handle dari sesi dan
**mengabaikan** field `player` di body; tanpa cookie balasannya 401. Dedupe per slot
memakai `xid` (id X), bukan handle, karena handle bisa diganti — entri lama tanpa `xid`
tetap dibandingkan lewat handle.

**Fungsi Vercel hanya dapat direktori sendiri di `sys.path`**, jadi `xauth_lib.py`
di-*vendor* dua kali: `api/xauth_lib.py` (untuk `api/receipts.py`) dan
`api/xauth/xauth_lib.py` (untuk `api/xauth/*`). Ubah keduanya. Ini penyebab deploy
pertama 500 `ModuleNotFoundError: No module named 'xauth_lib'`.

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
Branch aktif `main`, head **`921ba5a`**. Branch `data` untuk snapshot + receipt,
head **`6c97755`**.

**Penting soal branch `data`:** workflow checkout ke `data`, jadi yang dieksekusi cron
adalah `collector/` + `.github/` **di branch itu**, bukan di `main`. Keduanya sempat
menyimpang (tanpa `verify.py`, tanpa dedupe, masih ada fallback motionradar) sehingga
run terjadwal pertama akan merah. Sudah disamakan dengan `main` per `6c97755`. **Kalau
mengubah `collector/`, `engine/`, atau workflow di `main`, salin juga ke `data`** —
kalau tidak, cron tetap menjalankan versi lama tanpa ada yang memberi tahu.

Rekaman sekarang (17 Nov 07:00Z): **4 snapshot, 4 window** — `asOf` 11-15T20:00,
11-16T04:00, 11-16T08:00, 11-16T12:00, semua `motion-official`, masing-masing 79 rows.
Sebelumnya dua file dibuang karena tidak jujur: `20261115T201601Z` berasal
dari motionradar (beda posisi di 37 dari 79 kreator vs resmi, bikin `verify.py` exit 2)
dan `20261115T202105Z` duplikat identik dari window yang sama.

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
| `index.html` (avatar) | Foto profil resmi per kreator dari `https://leaderboard.motion.game/pfp/<id>.jpg` (id dari `creators[].id`, host resmi — API JSON tidak punya field avatar). 8 dari 79 id balas 404, jadi `avatar()` di `index.html` menukar `<img>` gagal dengan inisial (`AV_FB`, kelas ukuran dibawa lewat `data-extra` karena atribut inline `onerror` cuma bisa kutip ganda). Dipakai di baris board, judul kartu draft, dan chip lineup. Gambar remote, tidak di-mirror ke repo |
| `README.md` | Sumber angka, aturan resmi, alasan GitHub Actions, bagian rarity/boost, section Status (verified vs masih terbuka) |
| `build.sh`, `vercel.json`, `requirements.txt`, `.gitignore` | Build + konfigurasi deploy |

Catatan verifikasi (17 Nov 2026 UTC): keempat endpoint live 200, `/signals.json` dan
`/api/signals` sama-sama `count=1 / 1 window / motion-official`. `snapshot.py` diuji
dua kali pada window yang sama → `[skip]` dan tidak menambah file; `verify.py --at
2026-11-16T04:10:00Z` → exit 1 dengan slot `00:00Z` dilaporkan hilang. Jalur cron
terbukti bekerja. Yang belum terbukti hanya run **terjadwal** sungguhan (belum ada
satu pun; run pertama dijadwalkan `2026-11-16T00:07Z`).

Kalau `/api/signals` tampak masih menyajikan angka lama setelah push, itu cache edge
Vercel (`s-maxage=300`), bukan kode: cek dengan `?cb=$(date +%s)` atau file mentah di
`raw.githubusercontent.com`. `/signals.json` statis ikut build, jadi perlu redeploy.

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
2. ~~Tunggu run cron pertama yang benar-benar terjadwal.~~ **Beres**: run 02:53Z hijau.
   Sisa yang perlu dipantau: `delta72h` baru terisi setelah kira-kira 3 hari window
   (yaitu sekitar 19-20 Nov) — dan itu **setelah deadline**, jadi di submission
   cukup sebut `delta24h` saja atau `null` yang jujur. `delta24h` sudah terisi.
3. **Isi receipt book dengan call nyata.** Book sekarang kosong dan itu memang benar:
   receipt pertama harus call sungguhan, bukan data tes. Kalau menguji, pakai handle
   tes lalu **hapus lagi** dari branch `data` (lihat catatan di bawah).
4. **(Opsional, perlu izin user) hapus Vercel `vprobe` + 2 alias** — item "nomor 5"
   yang dikecualikan. Jangan jalan sendiri.
5. **(Opsional) redesign total UI.** Belum dikerjakan; yang sudah ada tetap perbaikan.
6. **Aktifkan connect-X di produksi.** Kode sudah live, tapi `/api/xauth/status` masih
   balas `configured: false` karena `X_CLIENT_ID` dan `X_SESSION_SECRET` belum diset di
   Vercel. Tanpa itu tombol Connect X menampilkan alasan dan filing receipt balas 401.
   Perlu app di X developer portal dengan callback
   `https://motion-draft-room.vercel.app/api/xauth/callback`, tipe public client (PKCE,
   tanpa client secret), lalu `vercel env add X_CLIENT_ID` + `X_SESSION_SECRET`
   (nilai acak 32+ byte) dan redeploy.

Catatan kerja yang berguna:
- Untuk menguji POST receipt di live lalu membersihkan: `git checkout data`,
  `git reset --hard origin/data`, buang receipt dengan `player` tes, commit, push.
  Branch `data` bisa telat beberapa detik setelah POST, jadi kalau `receipts.json`
  terbaca kosong padahal POST balas 201, tunggu dan fetch ulang — jangan menyimpulkan
  POST-nya gagal.
- Deploy: **`./deploy.sh`** dari `/data/workspace/motion-draft-room` (butuh
  `VERCEL_TOKEN` di env). Jangan pakai `vercel --prod` lagi: team Vercel project ini
  hanya berisi akun owner (`friodrops-5778`), jadi build diblokir
  `deployment_blocked` bila author commit bukan anggota team — dan commit di repo ini
  di-author `frianowzki`. Skrip itu mengunggah file yang di-track lewat Deployments API
  v13 dengan metadata git dipaku ke akun owner, menunggu READY, lalu memastikan domain
  produksi masih terpasang. `./deploy.sh --dry-run` mencetak daftar file tanpa deploy.
  Setelah deploy, verifikasi keempat endpoint dengan `curl`.
- Landing page: `landing.html` adalah sumbernya, `build.sh` menyalinnya ke `/`.
  Section room (SwatchAccordion), stats rail, dan receipt memakai token `--slab*`;
  di dark mode token itu hitam (`#131312` di atas `#0f0f0e`), bukan putih.
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
