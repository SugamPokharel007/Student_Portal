# Student Portal

A comprehensive student portal built with Django that helps manage academic resources including subjects, notes, question banks, and notices.

## Features

- Subject Management
- Notice Board
- Syllabus Management
- Question Bank
- Notes Management
- Contact System
- User Authentication

## Tech Stack

- Python 3.x
- Django
- HTML/CSS
- JavaScript
- SQLite (Database)

## Installation

1. Clone the repository
```bash
git clone <your-repository-url>
cd student-portal
```

2. Create a virtual environment
```bash
python -m venv myenv
```

3. Activate the virtual environment
```bash
# On Windows
myenv\Scripts\activate

# On macOS/Linux
source myenv/bin/activate
```

4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create a superuser
```bash
python manage.py createsuperuser
```

7. Run the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Project Structure

```
std_portal/
├── student_app/         # Main application
│   ├── static/         # Static files (CSS, JS)
│   ├── templates/      # HTML templates
│   ├── models.py       # Database models
│   ├── views.py        # View functions
│   └── urls.py         # URL configurations
├── std_portal/         # Project settings
└── manage.py           # Django management script
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 