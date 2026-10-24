
# SkillSwap

SkillSwap is a Django-based web application that helps people exchange skills and learn from one another. Users can create profiles, list their skills, send learning requests, communicate after a request is accepted, and rate learning sessions.

## Features

- User registration and authentication
- Profile creation and profile picture uploads
- Skills listing and matching
- Certifications management
- LinkedIn and GitHub profile links
- Skill exchange requests
- Accepting and rejecting learning requests
- Notifications
- Chat between eligible users
- Image, audio, and file sharing in chat
- Block and unblock users for privacy
- Ratings for completed learning sessions
- Django admin panel

## Technology Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL
- **Version Control:** Git and GitHub
- **Additional Tools:** Docker and Redis configuration

## Project Structure

```text
SkillSwap/
├── .github/
│   └── workflows/
├── accounts/
├── config/
├── learning/
├── skillswap/
├── swaps/
├── templates/
├── static/
├── media/
├── .env.example
├── .gitignore
├── docker-compose.redis.yml
├── manage.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

Replace the example URL with your actual GitHub repository URL.

```bash
git clone https://github.com/SWAPNILVERMA108/SkillSwap.git
cd YOUR_REPOSITORY
```

Alternatively, open your existing SkillSwap project folder in VS Code.

### 2. Create a Virtual Environment

For Windows CMD:

```cmd
python -m venv .venv
```

### 3. Activate the Virtual Environment

```cmd
.venv\Scripts\activate
```

### 4. Install Dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a local `.env` file from `.env.example`:

```cmd
copy .env.example .env
```

Open `.env` and configure the required environment variables.

Example configuration:

```dotenv
DJANGO_SECRET_KEY=your-local-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=skillswap
DB_USER=postgres
DB_PASSWORD=your-postgresql-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

**Important:** These variable names are examples. Use the exact variable names expected by your project's `config/settings.py` and `.env.example`.

Never upload `.env` or real credentials to GitHub.

### 6. Configure PostgreSQL

If your project uses PostgreSQL:

1. Start the PostgreSQL service.
2. Create the database specified in your environment configuration if it does not exist.
3. Verify the database username and password.
4. Confirm the database host and port.

### 7. Apply Database Migrations

Run:

```cmd
python manage.py migrate
```

### 8. Check Django Configuration

```cmd
python manage.py check
```

### 9. Create an Administrator Account (Optional)

```cmd
python manage.py createsuperuser
```

Follow the prompts to create the administrator account.

### 10. Run the Development Server

```cmd
python manage.py runserver
```

Open the application in your browser:

http://127.0.0.1:8000/

Stop the server by pressing `Ctrl + C` in the terminal.

## Testing

### Run Automated Tests

```cmd
python manage.py test
```

### Test Multiple Users

Register multiple accounts through the application or create test users using Django's shell:

```cmd
python manage.py shell
```

Example:

```python
from django.contrib.auth import get_user_model

User = get_user_model()

test_users = [
    ("alice_test", "alice@example.com", "TestPass123!"),
    ("bob_test", "bob@example.com", "TestPass123!"),
    ("charlie_test", "charlie@example.com", "TestPass123!"),
]

for username, email, password in test_users:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email},
    )

    if created:
        user.set_password(password)
        user.save()
        print(f"Created: {username}")
    else:
        print(f"Already exists: {username}")

exit()
```

This example assumes your custom user model supports `username` and `email`. Adjust it if your user model requires different fields.

Use separate browser sessions to test multiple accounts.

## Manual Testing Checklist

- [ ] Register and log in with different accounts.
- [ ] Test invalid login credentials.
- [ ] Update profiles and upload profile pictures.
- [ ] Add certifications and social links.
- [ ] Send a learning request.
- [ ] Accept or reject a learning request.
- [ ] Verify notifications.
- [ ] Send chat messages.
- [ ] Test supported file attachments.
- [ ] Verify that unauthorized users cannot access private chats.
- [ ] Test blocking and unblocking.
- [ ] Complete a learning session and submit ratings.

## Useful Django Commands

### Start the Server

```cmd
python manage.py runserver
```

### Check the Project

```cmd
python manage.py check
```

### Create Migrations

```cmd
python manage.py makemigrations
```

### Apply Migrations

```cmd
python manage.py migrate
```

### Run Tests

```cmd
python manage.py test
```

### Create an Administrator

```cmd
python manage.py createsuperuser
```

## Troubleshooting

### PostgreSQL Authentication Error

If you see a password authentication error:

- Confirm PostgreSQL is running.
- Check the database username and password in `.env`.
- Verify that the environment variable names match `config/settings.py`.
- Ensure the database exists.

### Missing Python Modules

Activate the virtual environment and run:

```cmd
pip install -r requirements.txt
```

### Port Already in Use

Run Django on another port:

```cmd
python manage.py runserver 8001
```

Then open:

http://127.0.0.1:8001/

## Security Notes

- Never commit `.env` or private credentials.
- Keep `.venv/`, Python caches, and private uploads out of Git.
- Set `DEBUG=False` before production deployment.
- Use a strong Django secret key.
- Configure allowed hosts and HTTPS appropriately.
- Validate uploaded files and enforce access permissions on private attachments.
- Verify authentication and authorization for chat, blocking, ratings, and profile operations.

## Future Improvements

- Expand automated testing.
- Improve real-time chat functionality if needed.
- Strengthen file-upload security.
- Improve mobile responsiveness.
- Add production deployment documentation.

## Author

**Swapnil Verma**

GitHub: https://github.com/SWAPNILVERMA108/SkillSwap.git

---

**Note:** Replace the example GitHub details and environment values with your actual project configuration before publishing.
