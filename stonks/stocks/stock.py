from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from stonks.user.models import User, Stock, Watchlist, database
from stonks.helper.extensions import cache

from datetime import datetime, timedelta
import requests

stock = Blueprint('stock', __name__)

@cache.memoize(timeout=600) # Cache for 10 minutes
def get_stock_news(symbol):
    """
    Get the latest 3 news for a stock at the watchlist using the Finnhub API

    Args:
        symbol (str): The stock symbol

    Returns:
        list: A list of news
    """
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    apikey = current_app.config['FINNHUB_API_KEY']
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={yesterday}&to={today}&token={apikey}"
    response =  requests.get(url)
    if response.status_code == 200:
        print(f"Requesting news for {symbol}")
        return response.json()[:3] # Return only the first 3 news
    return []

@stock.route('/watchlist', methods=['GET', 'POST'])
def watchlist_page():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()

        if not user.watchlist:
            user.watchlist = Watchlist(user=user)
            database.session.commit()

        user_watchlist = user.watchlist

        if request.method == 'POST':
            stock_symbol = request.form['stock']
            stock = Stock.query.filter_by(symbol=stock_symbol).first()

            if stock:
                user_watchlist.stocks.append(stock)
                database.session.commit()

                cache.delete_memoized(get_stock_news, stock_symbol)
            else:
                flash('Stock not found', 'danger')
            
            return redirect(url_for('stock.watchlist_page'))
        
        return render_template('stock/watchlist.html', watchlist=user_watchlist)
    else:
        flash('Please login to view your watchlist', 'danger')
        return redirect(url_for('auth.login'))
    
@stock.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()

        if not user.watchlist:
            flash('Watchlist not found', 'danger')
            return redirect(url_for('stock.watchlist_page'))

        user_watchlist = user.watchlist
        
        stock = Stock.query.filter_by(id=stock_id).first()

        if stock in user_watchlist.stocks:
            user_watchlist.stocks.remove(stock)
            database.session.commit()

            cache.delete_memoized(get_stock_news, stock.symbol)
        else:
            flash('Stock not found', 'danger')

    else:
        flash('Please login to view your watchlist', 'danger')
        return redirect(url_for('auth.login'))
    
    return redirect(url_for('stock.watchlist_page'))

@stock.route('/stock_details/<int:stock_id>')
def stock_details(stock_id):
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()

        if not user.watchlist:
            flash('Watchlist not found', 'danger')
            return redirect(url_for('stock.watchlist_page'))
        
        user_watchlist = user.watchlist
        
        stock = Stock.query.filter_by(id=stock_id).first()

        if stock in user_watchlist.stocks:
            return render_template('stock/stock_details.html', stock=stock)
        else:
            flash('Stock not found', 'danger')
            return redirect(url_for('stock.watchlist_page'))
    else:
        flash('Please login to view stock details', 'danger')
        return redirect(url_for('auth.login'))