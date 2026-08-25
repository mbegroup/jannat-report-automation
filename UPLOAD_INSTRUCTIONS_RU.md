# Как загрузить пакет в GitHub

1. Откройте `SMD-jannat/jannat-report-automation`.
2. Нажмите **Add file → Upload files**.
3. Откройте распакованную папку пакета и выделите **все файлы внутри**, а не саму внешнюю папку.
4. Убедитесь, что среди загруженных папок есть `.github`, `src`, `tests`, `sample_input` и `public`.
5. Внизу страницы нажмите **Commit changes**.
6. Перейдите во вкладку **Actions**.
7. Слева выберите **Process Jannat report**.
8. Нажмите **Run workflow → Run workflow**.
9. После зелёной галочки откройте запуск и скачайте artifact `jannat-consolidated-report`.

Если GitHub не показывает папку `.github` при выборе всей папки, выделите её вместе с остальными файлами вручную или загрузите содержимое ZIP через GitHub Desktop.
