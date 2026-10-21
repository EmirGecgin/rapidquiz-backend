# RapidQuiz Backend — CLAUDE.md

Bu dosya her fazdan sonra güncellenir. Yeni bir oturum başlarken önce bu dosyayı oku.

## Durum
- Son tamamlanan faz: **(henüz yok)**
- Sıradaki faz: **B1 — İskelet**
- Not: Frontend ayrı repoda (`rapidquiz-frontend`). Bu repo mobil istemcilere de hizmet verecek şekilde tasarlanıyor.

## Kurallar (her fazda geçerli)
- Puan, süre, sıralama YALNIZCA sunucuda hesaplanır. Doğru cevap bilgisi soru yanıtında asla dönmez.
- API sürümlü: `/api/v1/`. Çerez yok; oyun istekleri `X-Session-Token` başlığıyla doğrulanır.
- Hata biçimi: `{"error":{"code","message"}}`. Kodlar: `invalid_token, session_expired, session_finished, question_mismatch, already_answered, invalid_name, rate_limited, not_found, validation_error`.
- Sırlar ortam değişkenlerinden. Her faz testleriyle biter; testler geçmeden faz bitmez.
- Yalnızca istenen fazı yap.

## Teknoloji
Python 3.12, Django 5, DRF, PostgreSQL 16, gunicorn, whitenoise, django-cors-headers, dj-database-url, drf-spectacular, pytest-django.
Deploy: DigitalOcean App Platform — Docker service + Managed PostgreSQL.

## Oyun Mantığı
- Kategoriler (slug): `spor`, `genel-kultur`, `yazilim`, `yapay-zeka-teknoloji`, `tarih`. Kategori başına ≥30 soru havuzu.
- Tur: rastgele 10 soru, 4 kolay / 4 orta / 2 zor (eksikse diğer zorluklardan tamamla). 4 şık, tek doğru, şık sırası karışık.
- Puan: doğru +10, hız bonusu kalan tam saniye başına +1 (en fazla +4), yanlış −5, süre doldu −5. Skor 0'ın altına inmez (maks 140).
- Sunucu hesabı: `elapsed = answered_at − shown_at`; `elapsed > 5800ms` → süre doldu. Doğruysa `10 + min(4, floor((5000 − min(elapsed,5000))/1000))`. `total_answer_ms += min(elapsed,5000)`. `/next/` önceki cevapsız soruyu süre doldu olarak kapatır.
- Liderlik: kategori başına, `period=day|week|all`, varsayılan ilk 20, Europe/Istanbul. Sıra: score desc, total_answer_ms asc, finished_at asc. Yalnızca finished + isimli + gizli olmayan turlar.
- İsim: 2–20 karakter, harf (Türkçe dahil)/rakam/boşluk/`_-.`, kırpılır, TR/EN küfür filtresi.

## Veri Modeli
- **Category**: name(60), slug unique, icon(40), color(7), order, is_active
- **Question**: category FK, text(140), difficulty(easy/medium/hard), is_active, created_at
- **Choice**: question FK, text(60), is_correct — her soruda tam 4 şık, tam 1 doğru (Admin + `clean()`)
- **QuizSession**: id UUID, token(64, `secrets.token_urlsafe`), category FK, question_ids ArrayField, current_index, score, correct_count, total_answer_ms, status(active/finished/expired), player_name null, is_hidden, platform(web/ios/android), created_at, finished_at. İndeks: `(category, status, -score, total_answer_ms)`
- **SessionAnswer**: session FK, question FK, shown_at, answered_at null, choice FK null (null=süre doldu), is_correct, points. unique(session, question)

## API (`/api/v1`)
| Metot | Yol | Gövde → Yanıt |
|---|---|---|
| GET | `/health/` | → `{status:"ok"}` (DB kontrolü) |
| GET | `/categories/` | → `[{name,slug,icon,color,question_count}]` |
| POST | `/sessions/` | `{category,platform}` → `{session_id,token,total_questions,time_limit_ms}` |
| POST | `/sessions/{id}/next/` | → `{index,question_id,text,choices:[{id,text}],time_limit_ms}` veya `{done:true}` |
| POST | `/sessions/{id}/answer/` | `{question_id,choice_id\|null}` → `{is_correct,correct_choice_id,points,score,elapsed_ms}` |
| POST | `/sessions/{id}/finish/` | `{player_name}` → `{score,rank,correct_count}` |
| GET | `/leaderboard/{slug}/?period=&limit=` | → `[{rank,player_name,score,correct_count,finished_at}]` (limit ≤100) |
| GET | `/schema/`, `/docs/` | OpenAPI, Swagger |

Güvenlik: token `secrets.compare_digest`; throttling IP başına 10 tur/dk, 120 cevap/dk; 10 dk'dan eski aktif oturumlar `expire_sessions` komutuyla expired; prod'da `DEBUG=False`, `SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")`, Admin yolu `ADMIN_URL` env'den.

## Sorular
`fixtures/questions/<slug>.json` → `python manage.py load_questions <yol> [--dry-run]` (idempotent, aynı metin = güncelle).
```json
{"category":{"slug":"tarih","name":"Tarih","icon":"landmark","color":"#E8B4A0","order":5},
 "questions":[{"text":"İstanbul hangi yılda fethedildi?","difficulty":"easy","choices":["1453","1071","1299","1517"],"answer":0}]}
```
Soru ≤90, şık ≤30 karakter; olumsuz kalıp ve zamanla eskiyen soru yok; doğru şık indeksi dağıtılmış.
Renkler: spor `#8EC5E8`, genel-kultur `#F5C98B`, yazilim `#A9B8F0`, yapay-zeka-teknoloji `#C6A9E8`, tarih `#E8B4A0`.

## Deploy
- `Dockerfile`: python:3.12-slim, libpq5, requirements, `collectstatic` (build-only SECRET_KEY), root olmayan kullanıcı, `gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 3`.
- `docker-compose.yml` (yerel): postgres:16 + web (runserver, volume mount). `.env.example` ekle.
- `.do/app.yaml`: `databases` PG 16 (`db`); `services.api` dockerfile, http_port 8000, health `/api/v1/health/`, env `DATABASE_URL=${db.DATABASE_URL}`, SECRET_KEY, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, ADMIN_URL; `jobs.migrate` kind PRE_DEPLOY `python manage.py migrate --noinput`.

## Fazlar
- **B1** İskelet: settings (base/dev/prod), apps (catalog, game, leaderboard), Docker, compose, .env.example, CORS, exception handler, `/health/` + test.
- **B2** catalog: modeller, Admin (Choice inline, 4 şık/1 doğru doğrulaması), `/categories/`, `load_questions`, kategori başına 3 örnek soru.
- **B3** game: `services.py` (start_session, next_question, submit_answer, finish_session) + uçlar. Testler (`timezone.now` mock): 0.5 sn doğru +14, 4.9 sn +10, yanlış −5, 5.9 sn süre doldu −5, skor ≥0, çift cevap reddi, cevapsız `/next/` kapatma, 10 soru sonrası done, bitmemiş turda finish reddi.
- **B4** leaderboard: uç, filtreler, eşitlik kuralı, finish'teki rank aynı kuralla.
- **B5** güvenlik: throttling, küfür filtresi, is_hidden Admin aksiyonu, `expire_sessions`, prod güvenlik ayarları.
- **B6** drf-spectacular, `.do/app.yaml`, prod imajı yerelde doğrula, README.
- **C1** Her kategori için ayrı oturumda 30 soru (12 kolay/12 orta/6 zor), `--dry-run` ile doğrula. İnsan kontrolü şart.
