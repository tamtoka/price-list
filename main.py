import csv
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from playwright.sync_api import sync_playwright


# 1. Находим папку, в которой находится наша программа.
folder = Path(__file__).resolve().parent

# 2. Читаем товары из CSV.
with (folder / "products.csv").open(
    encoding="utf-8-sig", newline=""
) as file:
    reader = csv.DictReader(file)

    required_columns = {"product", "price", "qty"}
    if not required_columns.issubset(reader.fieldnames or []):
        raise ValueError("В CSV нужны столбцы: product,price,qty")

    items = list(reader)

if not items:
    raise ValueError("В CSV нет товаров.")

# 3. Загружаем шаблон и подставляем в него товары.
environment = Environment(
    loader=FileSystemLoader(str(folder), encoding="utf-8-sig"),
    autoescape=True,
    undefined=StrictUndefined,
)
template = environment.get_template("template.html")
filled_html = template.render(items=items)

# 4. Создаём папку для результата.
output_folder = folder / "output"
output_folder.mkdir(exist_ok=True)
pdf_path = output_folder / "price-list.pdf"

# 5. Открываем заполненный HTML в скрытом браузере и создаём PDF.
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    try:
        page = browser.new_page()
        page.set_content(filled_html, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
        )
    finally:
        browser.close()

print(f"Создан PDF с товарами: {len(items)}")
print(f"Файл: {pdf_path}")

# 6. Просим Windows открыть готовый PDF.
try:
    os.startfile(str(pdf_path))
except OSError:
    print("PDF сохранён, но открыть его автоматически не удалось.")
    print("Открой файл вручную из папки output.")