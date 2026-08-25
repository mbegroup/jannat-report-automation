# Подключение Telegram после проверки пилота

Текущий Cloudflare-бот отмечает наличие Excel и скриншота. Для передачи самого Excel в Python потребуется обновление Worker:

1. сохранить `file_id`, имя файла и дату сообщения в D1;
2. добавить закрытый маршрут скачивания Excel из Telegram;
3. вызвать GitHub `repository_dispatch` с типом `telegram_report_received`;
4. передать GitHub временную закрытую ссылку;
5. после обработки сохранить HTML в Cloudflare и отправить директору ссылку.

Секреты для этапа подключения:

- в Cloudflare: `GITHUB_DISPATCH_TOKEN`, `REPORT_DOWNLOAD_SECRET`;
- в GitHub Actions: `REPORT_DOWNLOAD_SECRET`;
- существующий Telegram-токен остаётся только в Cloudflare.

Не публикуйте эти значения в сообщениях и файлах. После успешной проверки ZIP обновление Worker можно выполнить отдельно с временным Cloudflare-токеном и сразу его удалить.

