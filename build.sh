#!/usr/bin/env bash
# Скрипт сборки для Render: ставит зависимости, собирает статику и
# накатывает миграции.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# На бесплатном тарифе Render нет доступа к Shell, поэтому демонстрационные
# данные и администратора удобно создать прямо во время сборки: достаточно
# задать переменную окружения SEED_DEMO=true. Команда идемпотентна, повторные
# сборки дубликатов не создают.
if [ "$SEED_DEMO" = "true" ]; then
  python manage.py seed_demo
fi
