# Introduction

A Flask-based web application that allows users to manage a personalized stock watchlist.

## 🚀 Features

- 🔐 **User Authentication** (Signup/Login/Logout)
- 📊 **Stock Watchlist** (Add, remove, and track stocks)
- 📰 **Real-time Stock News** (Yahoo! Finance integration)
- 📈 **Stock Price Updates** (Automatic daily updates)
- 📩 **Email Notifications** (Significant price changes & daily reports)
- 📉 **Historical Stock Data Visualization**
- 💾 **Download Watchlist as CSV**
- 🛠 **Profile Management**

## 🛠 Installation

1. **Clone the Repository**
    ```sh
    git clone https://github.com/funburak/Stonks.git
    cd Stonks
    ```

2. **Set Up Poetry**
    If you don't have Poetry installed, you can install it by following the instructions [here](https://python-poetry.org/docs/#installation).

3. **Install Dependencies**
    ```sh
    poetry install
    ```

4. **Set Up Environment Variables**
    Create a [.env](http://_vscodecontentref_/1) file in the root directory and add the following:
    ```env
    SECRET_KEY=your_secret_key
    SQLALCHEMY_DATABASE_URI=your_database_uri
    MAIL_USERNAME=your_gmail_username
    MAIL_PASSWORD=your_gmail_password_for_apps
    TZ=your_timezone
    CLOUDINARY_CLOUD_NAME=your_cloud_name
    CLOUDINARY_API_KEY=your_api_key
    CLOUDINARY_API_SECRET=your_api_secret
    ```

5. **Initialize the Database**
    ```sh
    poetry run flask db init
    poetry run flask db migrate
    poetry run flask db upgrade
    ```

6. **Run the Application**
    ```sh
    poetry run flask run
    ```

## 📄 Documentation

For detailed documentation, refer to the docs directory.

## Live Deployment

Stonks will be live on Render until 15 March 2025 at this [website](https://stonks-7s4w.onrender.com)