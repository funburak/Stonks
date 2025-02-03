from flask import Blueprint, render_template, flash, redirect, url_for, session
from stonks.user.models import User
from stonks.stocks.stock import get_stock_news

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
def homepage():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user and user.watchlist:
            stock_symbols = [stock.symbol for stock in user.watchlist.stocks]
            stock_news = {}

            for symbol in stock_symbols:
                stock_news[symbol] = get_stock_news(symbol)
            
            return render_template('homepage.html',stock_news=stock_news)        
    else:
        flash("You must be logged in to view this page", 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('homepage.html', stock_news={})