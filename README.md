# Bilgi Deposu — Telegram Bilgi Botu

Telegram grubunda soru-cevap kaydı tutan ve benzer sorulara otomatik yanıt veren bot.

## Özellikler

- Kalıcı veri (SQLite yerel / PostgreSQL Railway)
- `/ekle`, `/sil`, `/guncelle` (yetkililer)
- `/sorular [sayfa]`, `/bul <kelime>`
- Görsel/video ile soru ekleme
- Uzun cevaplarda otomatik mesaj bölme
- Türkçe bulanık eşleme

## Yerel geliştirme

```bash
git clone https://github.com/user1010xx/bilgideposu.git
cd bilgideposu
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/macOS
# .env dosyasını düzenleyin — bu dosya Git'e gitmez
python -m bot.main
```

### Telegram ayarları

1. [@BotFather](https://t.me/BotFather) → bot oluştur → `BOT_TOKEN`
2. `/setprivacy` → **Disable** (grup mesajlarını görmesi için)
3. Yetkili tanımı (birini veya ikisini kullanın):
   - **Kullanıcı adı (önerilen, Railway):** Telegram → Ayarlar → Kullanıcı adı (ör. `kadirbasgoren`) → `ADMIN_USERNAMES=kadirbasgoren`
   - **Sayısal ID:** [@userinfobot](https://t.me/userinfobot) → `ADMIN_IDS=123456789`

## Railway deploy

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub** → `bilgideposu`
2. **PostgreSQL** eklentisi ekleyin (kalıcı veri)
3. **Variables** (Settings → Variables):

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `BOT_TOKEN` | Evet | BotFather token |
| `ADMIN_IDS` | Hayır* | Örn. `8166633577` veya `111,222` |
| `ADMIN_USERNAMES` | Hayır* | Örn. `kadirbasgoren,admin2` (@ yok) |
| `DATABASE_URL` | Otomatik | PostgreSQL plugin bağlar |

\* `ADMIN_IDS` veya `ADMIN_USERNAMES` en az birinde tanımlı olmalı (ikisi birlikte de kullanılabilir).
| `ALLOWED_GROUP_IDS` | Hayır | Sadece belirli grup(lar) |
| `MATCH_THRESHOLD` | Hayır | Varsayılan `82` |

4. **Settings → Replicas: 1** (iki örnek = çift mesaj)
5. Yerelde bot çalışıyorsa **durdurun** (aynı token iki yerde olmasın)
6. Deploy tamamlanınca logda `Application started` görünür

`Procfile` → `worker: python -m bot.main` (HTTP port gerekmez, polling kullanır)

## Komutlar

| Komut | Kim |
|-------|-----|
| Soru yaz | Otomatik cevap |
| `/sorular [sayfa]` | Herkes |
| `/bul <kelime>` | Herkes |
| `/yardim` | Herkes |
| `/ekle <soru>` → medya? → cevap | Yetkili |
| `/guncelle <no> <cevap>` | Yetkili |
| `/sil <no>` veya `/sil <metin>` | Yetkili |
| `/iptal` | Yetkili (ekleme iptal) |

## Güvenlik

- `.env` ve token **asla** GitHub'a push edilmez (`.gitignore`)
- Gizli değerleri yalnızca Railway **Variables** veya yerel `.env` içinde tutun
- Token sızdıysa BotFather → `/revoke` ile yenileyin

## Test

```bash
pytest tests -v
```

## Proje yapısı

```
bilgideposu/
├── bot/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── cache.py
│   ├── singleton.py
│   ├── handlers/
│   └── utils/
├── tests/
├── data/              # gitignore (yerel DB)
├── requirements.txt
├── Procfile
├── railway.toml
└── .env.example
```

## Lisans

Bu depo özel kullanım içindir; kullanım koşullarını repo sahibi belirler.
