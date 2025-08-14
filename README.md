# UniShop - Django E‑Commerce

A professional, responsive e‑commerce site built with Django 5, Channels-ready ASGI, and a simple on-site product chat assistant. Features categories, products, product gallery, cart, checkout, user auth, admin CMS, search, discounts, and a floating chat widget restricted to website products.

## Quick start (VS Code)

1. Open this folder in VS Code.
2. Create and activate the virtual environment:
   - Linux/macOS:
     - `python3 -m venv .venv`
     - `source .venv/bin/activate`
   - Windows (PowerShell):
     - `py -3 -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Run migrations and collect static:
   - `python manage.py migrate`
   - `python manage.py collectstatic --noinput`
5. Create a superuser:
   - `python manage.py createsuperuser`
6. Start the dev server:
   - `python manage.py runserver`
7. Visit the app at `http://127.0.0.1:8000` and the admin at `/admin/`.

## Key URLs
- `/` Home with search, featured grid
- `/category/<slug>/` Category page
- `/product/<slug>/` Product detail with gallery
- `/cart/` Cart, quantity updates, checkout form
- `/register/`, `/login/`, `/logout/` Authentication
- `/api/chat/` Product assistant API (POST `message`)

## Media & static
- Uploads are stored in `media/` (Pillow installed)
- Static files live in `static/` (served via WhiteNoise in dev)

## Notes
- Chat assistant is rule-based and restricted to on-site products.
- For production, configure `ALLOWED_HOSTS`, database, and static hosting.
