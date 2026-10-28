# HızlıQuiz (RapidQuiz) — Backend

Girişsiz, hızlı bilgi yarışması oyunu. Oyuncu bir kategori seçer, 10 soruluk bir tur oynar — her
soru için 5 saniye vardır, ne kadar hızlı ve doğru cevaplarsa o kadar çok puan kazanır. Tur
bitince ismini yazar ve kategorinin liderlik tablosuna girer.

Bu repo, oyunun **Django / Django REST Framework backend API**'sini içerir. Frontend (Vue 3) ayrı
bir repoda: [rapidquiz-frontend](https://github.com/EmirGecgin/rapidquiz-frontend).

## Özellikler

- 5 kategori (Spor, Genel Kültür, Yazılım, Yapay Zeka & Teknoloji, Tarih), kategori başına geniş soru havuzu
- Oyun mantığı tamamen sunucuda: puan, süre ve doğru cevap kontrolü istemciye asla açık edilmez
- Hız bonuslu puanlama: doğru cevap +10, kalan her tam saniye için +1 (en fazla +4), yanlış/süre dolması −5
- Çerezsiz oturum doğrulama (`X-Session-Token` header'ı)
- Gün/hafta/tüm-zamanlar liderlik tabloları, eşitlik durumunda süre ve bitiş zamanına göre sıralama
- Hız sınırlama (throttling), küfür filtresi, süresi dolan oturumların otomatik temizlenmesi
- OpenAPI şeması ve Swagger arayüzü ile tam API dokümantasyonu
- Mobil istemcilere (iOS/Android) hizmet verecek şekilde tasarlandı (`platform` alanı)

## Teknoloji

Python 3.12, Django 5, Django REST Framework, PostgreSQL 16, gunicorn, whitenoise,
django-cors-headers, dj-database-url, drf-spectacular, pytest-django. Docker ile konteynerleştirilmiş,
DigitalOcean App Platform'a dağıtılacak şekilde yapılandırılmış.

## Mimari

- `config/` — Django proje ayarları (`settings/base|dev|prod.py`), URL yönlendirme, merkezi hata
  işleyici (tüm API hataları `{"error":{"code","message"}}` biçiminde döner)
- `apps/catalog/` — kategoriler ve sorular (model, admin, `/categories/` endpoint'i, soru yükleme komutu)
- `apps/game/` — oturum/oyun akışı (`start_session`, `next_question`, `submit_answer`,
  `finish_session`), puan/süre hesaplama, güvenlik (throttling, küfür filtresi, oturum süresi aşımı)
- `apps/leaderboard/` — liderlik tablosu sorgulama, dönemsel filtreler

## Yerel geliştirme

```bash
cp .env.example .env
docker compose up -d db
docker compose up -d web
docker compose exec web python manage.py migrate
```

API `http://localhost:8000/api/v1/` altında çalışır. Swagger arayüzü: `http://localhost:8000/api/v1/docs/`.

### Soruları yükleme

```bash
docker compose exec web python manage.py load_questions fixtures/questions/tarih.json
```

Her kategori için `fixtures/questions/<slug>.json` dosyası idempotenttir (aynı metinli soru güncellenir).
`--dry-run` ile kaydetmeden önizleme yapılabilir.

### Testler

```bash
docker compose exec web python -m pytest
```

### Yönetim komutları

- `load_questions <yol> [--dry-run]` — kategori + soru fixture'ı yükler.
- `expire_sessions` — 10 dakikadan eski aktif oturumları `expired` yapar (örn. cron ile periyodik çalıştırılır).

## API dokümantasyonu

- OpenAPI şeması: `GET /api/v1/schema/`
- Swagger UI: `GET /api/v1/docs/`

Ana uç noktalar: `GET /categories/`, `POST /sessions/`, `POST /sessions/{id}/next/`,
`POST /sessions/{id}/answer/`, `POST /sessions/{id}/finish/`, `GET /leaderboard/{slug}/`.

## Dağıtım (DigitalOcean App Platform)

`.do/app.yaml` tek bir DO App içinde şunları tanımlar:

- `databases.db`: Managed PostgreSQL 16
- `services.api`: bu repodaki `Dockerfile` ile derlenen backend servisi, health check `/api/v1/health/`
- `jobs.migrate`: her dağıtımdan önce (`PRE_DEPLOY`) `migrate --noinput` çalıştırır
- `static_sites.web`: `rapidquiz-frontend` reposundan derlenen statik frontend

Dağıtmadan önce `.do/app.yaml` içindeki `CHANGE_ME*` placeholder'ları gerçek domain değerleriyle,
`SECRET_KEY`'i ise dosyaya yazmadan doğrudan DO panelinden güçlü bir değerle güncelleyin.

```bash
doctl apps create --spec .do/app.yaml
```

### Prod image'ı yerelde doğrulama

```bash
docker compose build web
docker compose up -d db
docker run --rm --network backend_default \
  -e SECRET_KEY=local-smoke-test -e DATABASE_URL=postgres://rapidquiz:rapidquiz@db:5432/rapidquiz \
  -e ALLOWED_HOSTS=localhost -p 8001:8000 backend-web
curl http://localhost:8001/api/v1/health/
```

## Ortam değişkenleri

`.env.example` dosyasına bakın: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`,
`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `ADMIN_URL`.

## Geliştirme süreci

Bu proje [Claude Code](https://claude.com/claude-code) ile fazlara bölünerek geliştirildi; her
fazın kapsamı ve teknik kararları [`CLAUDE.md`](./CLAUDE.md) dosyasında kayıtlıdır.
