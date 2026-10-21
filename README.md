# RapidQuiz Backend

Girişsiz, hızlı bilgi yarışması — Django 5 / DRF backend. Web ve mobil istemcilere hizmet verir.
Detaylı spesifikasyon ve faz geçmişi için [`CLAUDE.md`](./CLAUDE.md).

## Teknoloji

Python 3.12, Django 5, DRF, PostgreSQL 16, gunicorn, whitenoise, django-cors-headers,
dj-database-url, drf-spectacular, pytest-django.

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

## Dağıtım (DigitalOcean App Platform)

`.do/app.yaml` tek bir DO App içinde şunları tanımlar:

- `databases.db`: Managed PostgreSQL 16
- `services.api`: bu repodaki `Dockerfile` ile derlenen backend servisi, health check `/api/v1/health/`
- `jobs.migrate`: her dağıtımdan önce (`PRE_DEPLOY`) `migrate --noinput` çalıştırır
- `static_sites.web`: `rapidquiz-frontend` reposundan derlenen statik frontend

Dağıtmadan önce `.do/app.yaml` içindeki `CHANGE_ME*` placeholder'ları gerçek domain/secret
değerleriyle güncelleyin (gerçek `SECRET_KEY` değerini dosyaya yazmak yerine DO panelinden girin).

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
