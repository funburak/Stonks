from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Response
from stonks.user.models import Stock, Watchlist, database
from stonks.helper.extensions import cache
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import yfinance as yf
import yahooquery as yq
import json
from collections import defaultdict
import logging
from tabulate import tabulate
import csv
import io

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
    try:
        news = yf.Search(symbol, news_count=3).news

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
    except Exception as e:
        logging.error(f"An error occurred while fetching news for {symbol}: {e}")
        return []

@stock.route('/search_stock')
@login_required
def search_stock():
    """
    Search for a stock using Yahoo! Finance API

    Returns:
        str: A JSON string containing search results
    """
    query = request.args.get('q').strip()
    if not query:
        logging.info("No query provided")
        return render_template('stock/watchlist.html', watchlist= current_user.watchlist, search_results=[])
    
    try:
        search_results = yq.search(query)

        if not search_results or not search_results["quotes"]:
            logging.info(f"No results found for {query}")
            flash(f'No results found for {query}', 'warning')
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
    """
    Add a stock to the current user's watchlist
    """
    symbol = request.form.get('symbol', ' ').strip().upper()

    if not symbol:
        flash('Invalid stock symbol', 'danger')
        return redirect(url_for('stock.watchlist_page'))
    
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()

        if not stock: # If the stock is not in the database, add it
            ticker = yf.Ticker(symbol)
            current_price = float(ticker.info.get('currentPrice', None))
            historical_data = ticker.history(period="3d", interval="1d")
            latest_percent_change = float(round(historical_data['Close'].pct_change().iloc[-1] * 100,2))
            last_updated_at = datetime.now()

            stock = Stock(symbol=symbol, current_price=current_price, percent_change=latest_percent_change, last_updated_at=last_updated_at)
            database.session.add(stock)
            database.session.commit()

        if stock and stock not in current_user.watchlist.stocks:
            current_user.watchlist.stocks.append(stock)
            database.session.commit()
            cache.delete_memoized(get_stock_news, symbol)
            logging.info(f"{symbol} added to {current_user.username} watchlist")
            flash(f"{symbol} added to watchlist", 'success')
            return redirect(url_for('stock.watchlist_page'))
        else:
            logging.info(f"{symbol} already in watchlist")
            flash(f"{symbol} already in watchlist", 'warning')

    except Exception as e:
        logging.error(f"An error occurred while adding the {symbol} to {current_user.username}'s watchlist: {e}")
        flash('An error occurred while adding the stock', 'danger')

    return redirect(url_for('stock.watchlist_page'))

@stock.route('/watchlist')
@login_required
def watchlist_page():
    """
    Watchlist page for the current user
    """
    if not current_user.watchlist:
        current_user.watchlist = Watchlist(user=current_user)
        database.session.commit()

    user_watchlist = current_user.watchlist

    return render_template('stock/watchlist.html', watchlist=user_watchlist)

@stock.route('/download-watchlist')
@login_required
def download_watchlist():
    """
    Download the watchlist as a CSV file
    """
    if not current_user.watchlist:
        flash('Watchlist not found', 'danger')
        return redirect(url_for('stock.watchlist_page'))

    user_watchlist = current_user.watchlist

    if not user_watchlist.stocks:
        flash('No stocks in the watchlist', 'danger')
        return redirect(url_for('stock.watchlist_page'))

    try:
        output = io.StringIO()
        fieldnames = ["Stock Symbol", "Current Price", "Percent Change", "Last Updated At"]

        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()  # Write column headers

        # Write stock data as dictionary
        for stock in user_watchlist.stocks:
            writer.writerow({
                "Stock Symbol": stock.symbol,
                "Current Price": f"{stock.current_price:.2f}",
                "Percent Change": f"{stock.percent_change:.2f}%",
                "Last Updated At": stock.last_updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        output.seek(0)

        response = Response(output.getvalue(), content_type="text/csv; charset=utf-8")
        response.headers["Content-Disposition"] = "attachment; filename=watchlist.csv"
        return response
    except Exception as e:
        logging.error(f"An error occurred while downloading the watchlist: {e}")
        flash('An error occurred while downloading the watchlist', 'danger')
        return redirect(url_for('auth.profile_page'))

def update_stock_prices_daily(app):
    """
    Update the stock prices every day and delete the stock that arent in any watchlist
    """
    stock_changes = defaultdict(list)
    with app.app_context():
        # Delete the stocks that arent in any watchlist
        stocks = Stock.query.filter(~Stock.watchlists.any()).all()
        for stock in stocks:
            logging.info(f"Deleting {stock.symbol}")
            database.session.delete(stock)
            database.session.commit()

        # Update the stock prices
        stocks = Stock.query.all()

        for stock in stocks:
            update_stock(stock, stock_changes)
            database.session.commit()
        
        if stock_changes:
            send_notification_mail(stock_changes)

def update_stock(stock: Stock, stock_changes):
    """
    Fetch the latest stock price for a given stock
    """
    last_updated_at = stock.last_updated_at
    if last_updated_at and (last_updated_at.date() == datetime.now().date()): # If the stock was updated today, no need to update
        return
    last_price = stock.current_price
    ticker = yf.Ticker(stock.symbol)
    stock.current_price = float(ticker.info.get('currentPrice', None))

    if last_price == stock.current_price:
        logging.info(f"No price change in {stock.symbol}")
        return

    if last_price and ((last_price / stock.current_price >= 1.02) or (last_price / stock.current_price <= 0.98)):
        logging.info(f"%2 price change in {stock.symbol}")
        users = [watchlist.user for watchlist in stock.watchlists]
        for user in users:
            if user.notification_enabled:
                stock_changes[user.email].append(stock.symbol)
    historical_data = ticker.history(period="3d", interval="1d")
    latest_percent_change = float(round(historical_data['Close'].pct_change().iloc[-1] * 100,2))
    stock.percent_change = latest_percent_change
    stock.last_updated_at = datetime.now()
    logging.info(f"Updated {stock.symbol} price")

def send_notification_mail(stock_changes):
    """
    Sends a notification mail to the users with the stock changes
    """
    mail_handler = current_app.extensions['mail_handler']
    if mail_handler.send_change_mail(stock_changes):
        logging.info("Notification mail send")
    else:
        logging.error("Failed to send notification mail")

@stock.route('/delete_stock/<int:stock_id>', methods=['POST'])
@login_required
def delete_stock(stock_id):
    """
    Delete a stock from the current user's watchlist
    """
    if not current_user.watchlist:
        flash('Watchlist not found', 'danger')
        return redirect(url_for('stock.watchlist_page'))
    
    user_watchlist = current_user.watchlist

    stock = Stock.query.filter_by(id=stock_id).first()

    if stock in user_watchlist.stocks:
        user_watchlist.stocks.remove(stock)
        database.session.commit()

        cache.delete_memoized(get_stock_news, stock.symbol)
        logging.info(f"{stock.symbol} deleted from {current_user.username} watchlist")
    else:
        flash('Stock not found', 'danger')

    return redirect(url_for('stock.watchlist_page'))

@stock.route('/stock_details/<int:stock_id>')
@login_required
def stock_details(stock_id):
    """
    Page to display the stock details for a given stock
    """
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

        percent_changes = daily_data['Close'].dropna().pct_change(fill_method=None).fillna(0).multiply(100).tolist()[1:]
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
        logging.error(f"Error occured while fetching stock details for {symbol}: {e}")
        return None
    
def generate_daily_report(app):
    """
    Generate a daily stock watchlist report for all users that has enabled notifications
    """
    with app.app_context():
        watchlists = Watchlist.query.all()
        mail_handler = current_app.extensions['mail_handler']

        for watchlist in watchlists:
            if not watchlist.user.notification_enabled or not watchlist.stocks:
                continue

            report_header = "📊 Daily Stock Watchlist Report\n\n"

            # Prepare table data
            table_data = []
            for stock in watchlist.stocks:
                stock_symbol = f"{stock.symbol}"
                stock_price = f"${stock.current_price:.2f}"
                stock_percent_change = f"{stock.percent_change:+.2f}%"  # Adds + or - sign
                table_data.append([stock_symbol, stock_price, stock_percent_change])

            # Format table
            report_table = tabulate(
                table_data, 
                headers=["Stock", "Price", "Change"], 
                tablefmt="orgtbl"  # Clean, readable format
            )

            # Final report
            report = report_header + "```\n" + report_table + "\n```"  # Markdown formatting for readability

            # Send email
            if mail_handler.send_watchlist_report([watchlist.user.email], report):
                logging.info(f"Report sent to {watchlist.user.username}")
            else:
                logging.info(f"Failed to send report to {watchlist.user.username}")