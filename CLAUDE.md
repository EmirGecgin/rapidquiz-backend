# RapidQuiz Backend — CLAUDE.md

Bu dosya her fazdan sonra güncellenir. Yeni bir oturum başlarken önce bu dosyayı oku.

## Durum
- **Faz dışı düzeltme (2026-10-21, F3 sırasında bulundu)**: `CORS_ALLOW_HEADERS`'a `x-session-token` eklendi (`config/settings/base.py`). corsheaders'ın varsayılan izinli header listesi oyun isteklerinin kullandığı `X-Session-Token`'ı içermiyordu — frontend gerçek tarayıcıda test edilirken preflight reddi olarak ortaya çıktı (Django test client CORS preflight'ını tam simüle etmediği için B1-B6 testlerinde yakalanmamıştı). Regresyon testi: `tests/test_cors.py`.
- Son tamamlanan faz: **C1 — her kategori için 30 soru** (2026-10-22)
- Sıradaki faz: **(yok — tüm backend fazları B1-B6 + C1 tamamlandı)**
- **⚠️ C1 ile ilgili kritik not — İNSAN KONTROLÜ YAPILMADI**: `fixtures/questions/*.json`'a her kategori için 30 soru (12 kolay/12 orta/6 zor) eklendi ve yüklendi. Sorular AI tarafından yazıldı; spec'in kendisi "İnsan kontrolü şart" diyor ve bu kontrol henüz yapılmadı — üretime almadan önce 150 sorunun tamamı (özellikle tarih/sayısal gerçekler: yıllar, rakamlar, isimler) bir insan tarafından doğrulanmalı. Otomatik doğrulanan şeyler: format (soru ≤90/şık ≤30 karakter, tam 4 şık, geçerli answer indeksi, kategori başına tam 12/12/6 zorluk dağılımı, doğru şık indeksi dağıtılmış ~8/8/7/7) — bkz. doğrulama scripti CLAUDE.md geçmişinde. FACTUAL DOĞRULUK DOĞRULANMADI. `python manage.py load_questions <dosya> --dry-run` ile önce her dosya denendi (idempotent — B2'nin 3 örnek sorusuyla metin eşleşenler güncellendi, eşleşmeyenler ek olarak kaldı, bu yüzden bazı kategoriler 30'dan biraz fazla soruya sahip — spec'in "≥30 soru havuzu" kuralını hâlâ karşılıyor). 40/40 backend testi hâlâ geçiyor, `/categories/` üzerinden soru sayıları doğrulandı (spor 33, genel-kültür 31, yazılım 30, yapay-zeka-teknoloji 32, tarih 30).
- B6'da yapılanlar: `GET /api/v1/schema/` (OpenAPI) ve `/api/v1/docs/` (Swagger UI) bağlandı; `game`/`leaderboard` view'larına `@extend_schema` + özel response serializer'ları (`SessionCreateResponseSerializer`, `NextQuestionResponseSerializer`, `AnswerResponseSerializer`, `FinishResponseSerializer`) eklendi — `manage.py spectacular --validate` artık 0 uyarı/0 hata ile temiz. `.do/app.yaml`: tek DO App içinde `databases.db` (PG16), `services.api` (bu repo, health `/api/v1/health/`), `jobs.migrate` (PRE_DEPLOY, `migrate --noinput`), `static_sites.web` (rapidquiz-frontend reposu, `VITE_API_BASE_URL` BUILD_TIME) — `CHANGE_ME*` placeholder'lar gerçek domain/secret ile değiştirilmeli. README.md dolduruldu (kurulum, test, deploy, prod image doğrulama adımları). Prod image gerçek `gunicorn` CMD'siyle (dev `runserver` override'ı olmadan) çalıştırılıp doğrulandı: `X-Forwarded-Proto: https` ile health 200, HSTS header aktif, whitenoise statik dosyaları ve Swagger UI'ı doğru serve ediyor, admin login'e yönlendiriyor — SECURE_SSL_REDIRECT olmadan (proxy header'sız) tüm istekler 301'e düşüyor, bu DO'nun gerçek LB'si arkasında beklenen/doğru davranış. 39/39 test hâlâ geçiyor, `manage.py check`/`makemigrations --check` temiz.
- B5'te yapılanlar: `apps/game/throttling.py` (`SessionCreateThrottle` scope=`session_create` 10/dk, `AnswerThrottle` scope=`answer_submit` 120/dk — `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`'te tanımlı, view'lara `throttle_classes` ile bağlı; aşım `rate_limited` koduna düşüyor). `apps/game/profanity.py`: TR/EN küfür kelime listesi + leet/aksan normalizasyonu (`contains_profanity`), `finish_session`'daki isim doğrulamasına eklendi (`invalid_name`). `apps/game/admin.py`: `QuizSessionAdmin` + "Seçili turları gizle/göster" toplu aksiyonları (`is_hidden`). `expire_sessions` komutu: 10 dakikadan eski `active` oturumları `expired` yapar (`created_at` bazlı), finished/expired turlara dokunmaz. `config/settings/prod.py`'ye `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*` eklendi — `manage.py check --deploy` ile doğrulandı (sadece test secret key ve B6'ya kalan drf-spectacular şema uyarıları var, kritik sorun yok). Testlerde throttling/cache testleri arasında sızıntı olmaması için `tests/conftest.py`'a her testten önce `cache.clear()` çalıştıran autouse fixture eklendi. 39/39 test geçti (küfür tespiti, throttle limiti aşımı, expire_sessions, expired oturumun `session_expired` ile reddi, profan isimle finish reddi), gerçek veriyle `expire_sessions` canlı doğrulandı.
- B4'te yapılanlar: `QuizSession.RANKING_ORDER = ("-score","total_answer_ms","finished_at")` eşitlik kuralı sabiti eklendi; `apps/game/services.py`'deki `compute_rank` artık genel `_better_than(reference, ordering_fields)` yardımcısıyla bu sabiti kullanıyor (B3'teki elle yazılmış Q zinciriyle matematiksel olarak aynı). `apps/leaderboard/services.py`: `GET /api/v1/leaderboard/<slug>/` için `get_leaderboard` — kategori başına, yalnızca finished+isimli+gizli-olmayan turlar, `QuizSession.RANKING_ORDER` ile sıralı; `period_start()` ile day/week/all (Europe/Istanbul, haftanın başı Pazartesi), limit varsayılan 20/maks 100 doğrulaması view'da (`validation_error`). 31/31 test geçti (sıralama, filtreler — unfinished/hidden/unnamed hariç, period=day/week, limit, geçersiz period/limit, ve **finish'teki rank ile leaderboard pozisyonunun aynı olduğunu doğrulayan uçtan uca tutarlılık testi**), `manage.py check` ve `makemigrations --check` temiz (yeni model yok, migration gerekmedi).
- B1'de yapılanlar: `config/settings/{base,dev,prod}.py`, `apps/{catalog,game,leaderboard}` (sadece AppConfig, modelsiz), `Dockerfile` (multi-stage, libpq5 runtime, build-only SECRET_KEY ile collectstatic), `docker-compose.yml` (postgres:16 + web, host portu 5433 — yerelde 5432 doluydu), `.env.example`, CORS (`django-cors-headers`), DRF `EXCEPTION_HANDLER` → `config/exceptions.py` (tüm hatalar `{"error":{"code","message"}}`'a sarılıyor; game app'i kendi exception sınıflarında `default_code` kullanarak `session_expired` vb. kodları aynen geçiriyor), `GET /api/v1/health/` (DB `SELECT 1` kontrolü) + testler.
- B2'de yapılanlar: `apps/catalog/models.py` (Category, Question, Choice + `validate_choice_set` yardımcı fonksiyonu, `Question.clean()` tutarlılık kontrolü), `admin.py` (QuestionAdmin + ChoiceInline, `ChoiceInlineFormSet.clean()` ile tam 4 şık/tam 1 doğru doğrulaması — kayıt öncesi admin formunda), `GET /api/v1/categories/` (aktif kategoriler, aktif soru `question_count` anotasyonu, `order` sırası), `load_questions` komutu (`fixtures/questions/<slug>.json`, idempotent — aynı (kategori, metin) ikilisi günceller, `--dry-run` atomik rollback, soru ≤90/şık ≤30 karakter + 4 şık/geçerli answer doğrulaması), 5 kategori için 3'er örnek soru fixture'ı yüklü.
- B3'te yapılanlar: `apps/game/models.py` (QuizSession UUID+ArrayField(question_ids)+index `(category,status,-score,total_answer_ms)`, SessionAnswer unique(session,question)), `apps/game/exceptions.py` (InvalidToken/SessionExpired/SessionFinished/QuestionMismatch/AlreadyAnswered/InvalidName — `default_code` üzerinden `config/exceptions.py`'daki merkezi handler'a otomatik geçiyor), `apps/game/services.py`: `start_session` (4 kolay/4 orta/2 zor seçim + eksikse diğer zorluklardan tamamlama, karışık sıra), `next_question` (önceki cevapsız soruyu süre doldu olarak kapatır, şıkları karıştırır, 10 soru sonrası `{done:true}`), `submit_answer` (`elapsed>5800ms` süre doldu, doğruysa `10+min(4,...)` hız bonusu, yanlış/süre doldu `-5`, skor 0 altına inmez, question_mismatch/already_answered kontrolleri), `finish_session` (isim 2-20 karakter + TR karakter regex doğrulaması — küfür filtresi B5'te, tamamlanmamış turu `validation_error` ile reddeder, `compute_rank` — score desc/total_answer_ms asc/finished_at asc eşitlik kuralı, B4'te leaderboard'da aynen kullanılacak). Token `secrets.token_urlsafe(48)` (tam 64 karakter) + `secrets.compare_digest` ile doğrulanıyor. Testler: `timezone.now` mock ile (`apps.game.services.timezone.now` patch) — 0.5sn +14, 4.9sn +10, yanlış -5, 5.9sn süre doldu -5, skor≥0, çift cevap reddi, cevapsız next kapatma, 10 soru sonrası done, bitmemiş turda finish reddi, finish happy-path (rank/score/correct_count), invalid token, question_mismatch. 23/23 test geçti, `manage.py check` temiz, gerçek veriyle (tarih kategorisi, 3 soru) uçtan uca curl ile doğrulandı.
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
