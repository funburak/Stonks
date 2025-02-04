from flask import Blueprint, render_template, flash, redirect, url_for, session
from stonks.stocks.stock import get_stock_news
from flask_login import current_user

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
def homepage():
    if current_user.is_authenticated:
        if current_user and current_user.watchlist:
            stock_symbols = [stock.symbol for stock in current_user.watchlist.stocks]
            stock_news = {}

            for symbol in stock_symbols:
                stock_news[symbol] = get_stock_news(symbol)

            return render_template('homepage.html', stock_news=stock_news)
        else:
            flash("You must be logged in to view this page", 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('homepage.html', stock_news={})