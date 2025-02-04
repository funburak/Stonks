from flask import Blueprint, render_template, request, redirect, url_for, flash
from stonks.user.models import Stock, Watchlist, database
from stonks.helper.extensions import cache
from flask_login import login_required, current_user
from datetime import datetime
import yfinance as yf
import yahooquery as yq

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
            "publishTime": datetime.fromtimestamp(article['providerPublishTime']).strftime("%d %B %Y %H:%M UTC"),
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
            stock = Stock(symbol=symbol)
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

    return render_template('stock/watchlist.html', watchlist=user_watchlist)
    
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
    
    user_stocks = current_user.watchlist.stocks

    stock = Stock.query.filter_by(id=stock_id).first()

    if stock and stock in user_stocks:
        stock_symbol = stock.symbol

        try:
            # Fetch stock data using yfinance
            ticker = yf.Ticker(stock_symbol)
            data = ticker.history(period="1d")

            # Check if data is empty
            if data.empty:
                flash('Stock data not found', 'danger')
                return redirect(url_for('stock.watchlist_page'))
            
            latest_data = data.iloc[-1]
            
            # Extract stock data
            stock_data = {
                "symbol": stock_symbol,
                "open_price": float(latest_data["Open"]),
                "high_price": float(latest_data["High"]),
                "low_price": float(latest_data["Low"]),
                "close_price": float(latest_data["Close"]),
            }

            print(stock_data)

            # Render the stock details page with stock data
            return render_template('stock/stock_details.html', stock_data=stock_data)

        except Exception as e:
            print(e)
            flash('An error occurred while fetching stock data', 'danger')
            return redirect(url_for('stock.watchlist_page'))
    
    flash('Stock not found in your watchlist', 'danger')
    return redirect(url_for('stock.watchlist_page'))
