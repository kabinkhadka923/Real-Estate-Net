# 🏠 Gorkha Real Estate

A modern real estate platform built with Django for property listings, user management, and premium services.

## 🚀 Quick Start

### Requirements
- Python 3.8+
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:rojinat75/Real-Estate-Net.git
   cd real-estate-net
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv real_estate_env
   # Windows:
   real_estate_env\Scripts\activate
   # macOS/Linux:
   source real_estate_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database**
   ```bash
   python manage.py migrate
   ```

5. **Create admin user** (optional for development)
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000` to access the website!
<img width="1919" height="1079" alt="Screenshot 2026-01-02 205540" src="https://github.com/user-attachments/assets/30c0d449-2a72-4a75-8c48-04d6db09d7c9" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/f69a9a4c-728b-42b0-a3dc-b3fd4276626d" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/fee4fb71-db22-46db-9d14-de97c83bf917" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/3709b8c9-042a-40fe-be92-423f830fad4a" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/bbc14ad0-fc9d-4c0a-a256-067af07c7140" />
<img width="1919" height="927" alt="Screenshot 2026-01-02 210323" src="https://github.com/user-attachments/assets/c72b7f39-0ea9-41c1-ae16-deda55189050" />


## ✨ Features

- **🏢 Property Management**: List and manage real estate properties
- **👤 User Authentication**: Sign up, login, and user profiles
- **🔍 Advanced Search**: Filter properties by location, price, type
- **💎 Premium Services**: Subscription-based premium listings
- **📊 Analytics Dashboard**: Track website performance
- **📱 Responsive Design**: Mobile-friendly interface
- **📰 Blog**: Property news and market updates
- **📞 Contact System**: Inquire about properties

## 📁 Project Structure

```
├── accounts/         # User authentication and profiles
├── properties/       # Property listings and management
├── premium/          # Premium subscription features
├── analytics/        # Website analytics and tracking
├── contact/          # Contact forms and inquiries
├── blog/            # Blog articles and posts
├── legal/           # Legal pages and agreements
├── static/          # CSS, JavaScript, and images
├── templates/       # HTML templates
└── real_estate/     # Django project settings
```

## 🛠️ Tech Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Django Allauth (social login support)
- **Forms**: Django Crispy Forms

## 📝 Environment Variables

Create a `.env` file in the project root with your configuration:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3

⚠️Note⚠️: db.sqlite3 is temporarily committed for team development and testing.
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License



**Made with ❤️ for the global real estate community**
