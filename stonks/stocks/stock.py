from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from stonks.user.models import Stock, Watchlist, database
from stonks.helper.extensions import cache, scheduler
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import yfinance as yf
import yahooquery as yq
import json

stock = Blueprint('stock', __name__)

@cache.memoize(timeout=600) # Cache for 10 minutes
def get_stock_news(symbol):
    """
    Get the latest 3 news for a stock at the watchlist using Yahoo! Finance API

    Args:
        symbol (str): The stock symbol

    Returns:
        list: A list of news
    """
    news = yf.Search(symbol, news_count=3).news
    print(f"Requesting news for {symbol}")

    # Filter the response
    filtered_news = []
    for article in news:
        filtered_news.append({
            "title": article['title'],
            "link": article['link'],
            "publishTime": datetime.fromtimestamp(article['providerPublishTime']).strftime("%d %B %Y %H:%M"),
            "thumbnail": article['thumbnail']['resolutions'][0]['url'] if 'thumbnail' in article else None
        })

    return filtered_news

@stock.route('/search_stock')
@login_required
def search_stock():
    query = request.args.get('q').strip()
    if not query:
        return render_template('stock/watchlist.html', watchlist= current_user.watchlist, search_results=[])
    
    try:
        search_results = yq.search(query)

        if not search_results or "quotes" not in search_results:
            return render_template('stock/watchlist.html', watchlist= current_user.watchlist, search_results=[])
        
        results = []
        for stock in search_results["quotes"]:
            results.append({
                "symbol": stock.get("symbol"),
                "name": stock.get("shortname", stock.get("longname", "Unknown Company"))
            })
        
        return render_template('stock/watchlist.html', watchlist= current_user.watchlist, search_results=results)
    
    except Exception as e:
        flash('An error occurred while searching for the stock', 'danger')
        return render_template('stock/watchlist.html', watchlist= current_user.watchlist, search_results=[])

@stock.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    symbol = request.form.get('symbol', ' ').strip().upper()

    if not symbol:
        flash('Invalid stock symbol', 'danger')
        return redirect(url_for('stock.watchlist_page'))
    
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()

        if not stock: # If the stock is not in the database, add it
            ticker = yf.Ticker(symbol)
            current_price = ticker.info['currentPrice']
            historical_data = ticker.history(period="3d", interval="1d")
            latest_percent_change = round(historical_data['Close'].pct_change().iloc[-1] * 100,2)
            last_updated_at = datetime.now()

            stock = Stock(symbol=symbol, current_price=current_price, percent_change=latest_percent_change, last_updated_at=last_updated_at)
            database.session.add(stock)
            database.session.commit()

        if stock and stock not in current_user.watchlist.stocks:
            current_user.watchlist.stocks.append(stock)
            database.session.commit()
            cache.delete_memoized(get_stock_news, symbol)
            flash(f"{symbol} added to watchlist", 'success')
            return redirect(url_for('stock.watchlist_page'))
        else:
            flash(f"{symbol} already in watchlist", 'warning')

    except Exception as e:
        flash('An error occurred while adding the stock', 'danger')

    return redirect(url_for('stock.watchlist_page'))

@stock.route('/watchlist')
@login_required
def watchlist_page():
    if not current_user.watchlist:
        current_user.watchlist = Watchlist(user=current_user)
        database.session.commit()

    user_watchlist = current_user.watchlist

    # if user_watchlist.stocks:
    #     if update_stock_prices(user_watchlist.stocks):
    #         flash(f"Stock prices updated successfully", 'success')
    #     else:
    #         flash(f"An error occurred while updating stock prices", 'danger')

    return render_template('stock/watchlist.html', watchlist=user_watchlist)

def update_stock_prices_daily(app):
    """"Update the stock prices every day and delete the stock that arent in any watchlist"""
    print("Updating stock prices")

    with app.app_context():
        # Delete the stocks that arent in any watchlist
        stocks = Stock.query.filter(~Stock.watchlists.any()).all()
        for stock in stocks:
            database.session.delete(stock)
            database.session.commit()

        # Update the stock prices
        stocks = Stock.query.all()

        for stock in stocks:
            update_stock(stock)
            database.session.commit()

def update_stock(stock: Stock):
    """
    Fetch the latest stock price for a given stock
    """
    ticker = yf.Ticker(stock.symbol)
    stock.current_price = ticker.info['currentPrice']
    historical_data = ticker.history(period="3d", interval="1d")
    latest_percent_change = round(historical_data['Close'].pct_change().iloc[-1] * 100,2)
    stock.percent_change = latest_percent_change
    stock.last_updated_at = datetime.now()
    print(f"Updated {stock.symbol}")

def update_stock_prices(stocks):
    """"
    Update the prices of the stocks in the user's watchlist if a day has passed since the last update

    Args:
        stocks (list): A list of Stock objects

    Returns:
        bool: True if the prices were updated successfully, False otherwise
    """
    try:
        for stock in stocks:
            ticker = yf.Ticker(stock.symbol)
            today = datetime.now()
            last_update_time = stock.last_updated_at
            if today - last_update_time > timedelta(days=1):
                print(f"Updating {stock.symbol}")
                stock.current_price = ticker.info['currentPrice']
                historical_data = ticker.history(period="3d", interval="1d")
                latest_percent_change = round(historical_data['Close'].pct_change().iloc[-1] * 100,2)
                stock.percent_change = latest_percent_change
                stock.last_updated_at = today
                database.session.commit()
            else:
                print(f"Skipping update for {stock.symbol}")
        return True
    except Exception as e:
        print("Error:", e)
        return False

@stock.route('/delete_stock/<int:stock_id>', methods=['POST'])
@login_required
def delete_stock(stock_id):
    if not current_user.watchlist:
        flash('Watchlist not found', 'danger')
        return redirect(url_for('stock.watchlist_page'))
    
    user_watchlist = current_user.watchlist

    stock = Stock.query.filter_by(id=stock_id).first()

    if stock in user_watchlist.stocks:
        user_watchlist.stocks.remove(stock)
        database.session.commit()

        cache.delete_memoized(get_stock_news, stock.symbol)
    else:
        flash('Stock not found', 'danger')

    return redirect(url_for('stock.watchlist_page'))

@stock.route('/stock_details/<int:stock_id>')
@login_required
def stock_details(stock_id):
    if not current_user.watchlist:
        flash('Watchlist not found', 'danger')
        return redirect(url_for('stock.watchlist_page'))

    stock = Stock.query.filter_by(id=stock_id).first()

    if stock and stock in current_user.watchlist.stocks:
        stock_symbol = stock.symbol

        stock_data = get_stock_details(stock_symbol)

        if not stock_data:
            flash('Stock data not found', 'danger')
            return redirect(url_for('stock.watchlist_page'))
                
        return render_template('stock/stock_details.html', stock_data=stock_data)
    
    flash('Stock not found in your watchlist', 'danger')
    return redirect(url_for('stock.watchlist_page'))

def get_stock_details(symbol):
    """
    Get stock details for a given symbol using Yahoo! Finance API

    Args:
        symbol (str): The stock symbol

    Returns:
        str: A JSON string containing stock data
    """
    try:
        ticker = yf.Ticker(symbol)

        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)

        historical_data = ticker.history(period="7d", interval="1h")

        if historical_data.empty:
            return None

        company_name = ticker.info.get('longName', symbol)

        dates = historical_data.index.strftime("%d %B %Y %H:%M").tolist()
        closing_prices = historical_data['Close'].tolist()

        daily_data = historical_data.resample('1D').last()
        daily_data = daily_data[daily_data.index.dayofweek < 5]

        percent_changes = daily_data['Close'].pct_change().fillna(0).multiply(100).tolist()[1:]
        daily_dates = daily_data.index.strftime("%d %B").tolist()[1:]

        volume = historical_data['Volume'].tolist()

        stock_data = {
            "symbol": symbol,
            "company_name": company_name,
            "open_price": round(historical_data['Open'].iloc[-1], 2) if 'Open' in historical_data.columns else None,
            "high_price": round(historical_data['High'].iloc[-1], 2) if 'High' in historical_data.columns else None,
            "low_price": round(historical_data['Low'].iloc[-1], 2) if 'Low' in historical_data.columns else None,
            "close_price": round(historical_data['Close'].iloc[-1], 2) if 'Close' in historical_data.columns else None,
            "dates": dates,
            "closing_prices": closing_prices,
            "percent_changes": percent_changes,
            "daily_dates": daily_dates,
            "trading_volumes": volume
        }

        return json.dumps(stock_data)
    except Exception as e:
        print("Error:", e)
        return None