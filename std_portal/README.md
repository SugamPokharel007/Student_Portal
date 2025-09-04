# 🎓 Sikshya Kendra - Enhanced Academic Portal

A comprehensive, modern academic portal built with Django that provides students with access to educational resources, study materials, and collaborative learning tools. This enhanced version includes advanced features like intelligent search, contributor management, subscription systems, and analytics.

## ✨ Key Features

### 🎨 **Modern UI/UX Design**
- **Dark/Light Mode Toggle** - User preference-based theme switching
- **Responsive Design** - Mobile-first approach with Bootstrap 5
- **Smooth Animations** - AOS (Animate On Scroll) library integration
- **Modern Typography** - Inter font family for better readability
- **Interactive Elements** - Hover effects, transitions, and micro-interactions

### 🔍 **Advanced Search & Discovery**
- **TF-IDF Algorithm** - Intelligent search ranking based on content relevance
- **Multi-Filter Search** - Filter by faculty, subject, year, and resource type
- **Advanced Search Page** - Dedicated search interface with sorting options
- **Search Suggestions** - Real-time search suggestions (AJAX-ready)
- **Grid/List View Toggle** - Flexible result display options

### 👥 **Role-Based Access Control**
- **Student Role** - Access to approved resources and basic features
- **Contributor Role** - Upload and manage educational content
- **Admin Role** - Full administrative control and content approval
- **Contributor Request System** - Students can apply to become contributors

### 📊 **Analytics & Tracking**
- **Download Analytics** - Track resource downloads and user behavior
- **View Tracking** - Monitor content popularity and engagement
- **Trending Subjects** - AI-powered trending content detection
- **User Activity Dashboard** - Personal analytics and progress tracking
- **Admin Analytics** - Comprehensive admin dashboard with insights

### 💳 **Subscription System**
- **Three-Tier Plans** - Monthly, Semi-Yearly, and Yearly subscriptions
- **Premium Content Access** - Exclusive resources for subscribers
- **Automatic Expiry Management** - Smart subscription lifecycle handling
- **Expiry Notifications** - Proactive alerts for subscription renewal

### 📚 **Enhanced Resource Management**
- **File Upload Validation** - Support for PDF, DOC, DOCX, TXT, PPT, PPTX
- **Content Approval Workflow** - Admin review and approval system
- **Tagging System** - Categorize resources with custom tags
- **Version Control** - Track resource updates and modifications
- **Download Tracking** - Monitor resource usage and popularity

### 🎯 **Smart Features**
- **Intelligent Search** - TF-IDF based content ranking
- **Trending Detection** - Algorithm to identify popular subjects
- **Personalized Dashboard** - Role-based dashboard with relevant information
- **Smart Notifications** - Context-aware alerts and reminders
- **Auto-Complete Search** - Enhanced search experience

## 🛠️ Technology Stack

### Backend
- **Django 4.2+** - Web framework
- **Python 3.x** - Programming language
- **SQLite** - Database (production-ready with PostgreSQL)
- **Django Crispy Forms** - Enhanced form rendering
- **Django Taggit** - Tagging system
- **Django Filter** - Advanced filtering capabilities

### Frontend
- **Bootstrap 5** - CSS framework
- **Font Awesome 6** - Icon library
- **Inter Font** - Modern typography
- **AOS Library** - Scroll animations
- **Vanilla JavaScript** - Interactive features

### Development Tools
- **Django Debug Toolbar** - Development debugging
- **Django Extensions** - Additional development utilities
- **WhiteNoise** - Static file serving
- **Python Decouple** - Environment variable management

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd std_portal
```

### Step 2: Create Virtual Environment
```bash
python -m venv myenv

# On Windows
myenv\Scripts\activate

# On macOS/Linux
source myenv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth Credentials (Optional - for social login)
# Get these from: https://console.developers.google.com/
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here

# Facebook OAuth Credentials (Optional - for social login)
# Get these from: https://developers.facebook.com/
FACEBOOK_APP_ID=your-facebook-app-id-here
FACEBOOK_APP_SECRET=your-facebook-app-secret-here
```

### Step 5: Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

### Step 8: OAuth Setup (Optional)
To enable Google and Facebook login:

1. **Google OAuth Setup:**
   - Go to [Google Cloud Console](https://console.developers.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs: `http://localhost:8000/oauth/google/callback/`
   - Copy Client ID and Client Secret to your `.env` file

2. **Facebook OAuth Setup:**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Create a new app
   - Add Facebook Login product
   - Configure OAuth settings
   - Add authorized redirect URIs: `http://localhost:8000/oauth/facebook/callback/`
   - Copy App ID and App Secret to your `.env` file

## 📁 Project Structure

```
std_portal/
├── student_app/                 # Main application
│   ├── models.py               # Database models (enhanced)
│   ├── views.py                # View functions (enhanced)
│   ├── forms.py                # Form definitions (enhanced)
│   ├── urls.py                 # URL routing (enhanced)
│   ├── admin.py                # Admin interface (enhanced)
│   ├── static/                 # Static assets
│   │   ├── css/               # Stylesheets
│   │   ├── js/                # JavaScript files
│   │   └── images/            # Image assets
│   └── templates/             # HTML templates (enhanced)
│       ├── base.html          # Base template (modernized)
│       ├── home.html          # Home page (enhanced)
│       ├── dashboard.html     # Dashboard (new)
│       ├── advanced_search.html # Advanced search (new)
│       └── contributor_request.html # Contributor form (new)
├── std_portal/                # Project settings
│   ├── settings.py            # Django configuration (enhanced)
│   ├── urls.py                # Main URL routing
│   └── wsgi.py                # WSGI configuration
├── media/                     # User uploads
│   ├── notes/                 # Study notes
│   ├── question_banks/        # Question collections
│   ├── syllabus/              # Course syllabi
│   └── avatars/               # User profile pictures
├── requirements.txt           # Python dependencies (enhanced)
├── .env                       # Environment variables
└── README.md                  # Project documentation
```

## 🎯 Key Enhancements

### 1. **Enhanced Models**
- Added `ContributorRequest` model for contributor applications
- Enhanced `ContactMessage` with status tracking and admin responses
- Added `DownloadLog` and `ViewLog` for analytics
- Improved `UserProfile` with role management and statistics
- Added tagging support to all resource models

### 2. **Advanced Search System**
- TF-IDF algorithm implementation for intelligent search
- Multi-filter search with faculty, subject, year, and resource type
- Advanced search page with sorting options
- Real-time search suggestions (AJAX-ready)

### 3. **Modern UI/UX**
- Dark/Light mode toggle with persistent preferences
- Responsive design with Bootstrap 5
- Smooth animations and transitions
- Modern typography with Inter font
- Interactive elements and micro-interactions

### 4. **Role-Based Access Control**
- Student, Contributor, and Admin roles
- Contributor request and approval system
- Role-based dashboard and permissions
- Enhanced admin interface with custom actions

### 5. **Analytics & Tracking**
- Download and view tracking for all resources
- Trending subjects detection algorithm
- User activity analytics
- Admin dashboard with comprehensive statistics

### 6. **Subscription System**
- Three-tier subscription plans
- Automatic expiry management
- Premium content access control
- Subscription status tracking and notifications

### 7. **Social Authentication**
- Google OAuth integration
- Facebook OAuth integration
- Seamless user registration and login
- Automatic user profile creation

## 🔧 Configuration

### Environment Variables
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### File Upload Settings
- Maximum file size: 10MB
- Supported formats: PDF, DOC, DOCX, TXT, PPT, PPTX
- Organized file structure in media directory

### Cache Configuration
- Local memory cache for development
- Redis cache recommended for production

## 🚀 Production Deployment

### 1. **Database Setup**
```bash
# For PostgreSQL
pip install psycopg2-binary
```

### 2. **Static Files**
```bash
python manage.py collectstatic
```

### 3. **Environment Variables**
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 4. **Security Settings**
- HTTPS enforcement
- Secure headers configuration
- CSRF protection
- XSS protection

## 📊 Admin Features

### Enhanced Admin Interface
- **Custom Actions** - Bulk approve/reject resources
- **Inline Editing** - Quick edit capabilities
- **Analytics Dashboard** - Admin statistics and insights
- **User Management** - Enhanced user administration
- **Content Moderation** - Streamlined approval process

### Admin Actions
- Approve/Reject contributor requests
- Manage resource approvals
- View analytics and statistics
- Handle user feedback and support tickets

## 🔍 Search Features

### Basic Search
- Simple keyword search across all resources
- Faculty and subject filtering
- Quick access from navigation

### Advanced Search
- TF-IDF based intelligent ranking
- Multiple filter combinations
- Sorting options (relevance, date, popularity)
- Grid/List view toggle
- Search term highlighting

## 👥 User Roles & Permissions

### Student
- Access approved resources
- Download study materials
- Submit contributor requests
- View personal analytics

### Contributor
- Upload educational resources
- Manage own content
- Track upload statistics
- Access contributor dashboard

### Admin
- Full system administration
- Content approval and moderation
- User management
- Analytics and reporting
- System configuration

## 📈 Analytics & Reporting

### User Analytics
- Download history
- Search patterns
- Resource preferences
- Activity tracking

### Content Analytics
- Popular resources
- Trending subjects
- Download statistics
- User engagement metrics

### Admin Reports
- System usage statistics
- User growth metrics
- Content quality metrics
- Performance indicators

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Install development dependencies
pip install flake8 black isort

# Run code formatting
black .
isort .
flake8 .
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive CSS framework
- Font Awesome for the icon library
- All contributors and users of Sikshya Kendra

## 📞 Support

For support and questions:
- Email: support@sikshyakendra.edu.np
- Documentation: [Project Wiki]
- Issues: [GitHub Issues]

---

**Sikshya Kendra** - Empowering Education Through Technology 🎓 