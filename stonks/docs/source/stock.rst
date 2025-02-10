Stock Blueprint
===============

The `stock` Blueprint manages all stock-related routes, including searching for stocks, adding/removing stocks from the user's watchlist, fetching stock details, and generating daily reports.

.. automodule:: stock
   :members:
   :undoc-members:
   :show-inheritance:

Routes
------

Search for Stocks
~~~~~~~~~~~~~~~~~

Handles searching for stocks based on user input.

**Route:** `/search_stock`  
**Methods:** `GET`  
**Authentication:** Required  

**Query Parameters:**
- `q` (string) – The stock symbol or name to search for.

**Response:**
- Renders the `stock/watchlist.html` template with search results.

---

Add a Stock
~~~~~~~~~~~

Allows the user to add a stock to their watchlist.

**Route:** `/add_stock`  
**Methods:** `POST`  
**Authentication:** Required  

**Form Parameters:**
- `symbol` (string) – The stock symbol to add.

**Response:**
- Redirects to the watchlist page and flashes success or error messages.

---

View Watchlist
~~~~~~~~~~~~~~

Displays the user's stock watchlist.

**Route:** `/watchlist`  
**Methods:** `GET`  
**Authentication:** Required  

**Response:**
- Renders the `stock/watchlist.html` template with the user's watchlist.

---

Delete a Stock
~~~~~~~~~~~~~~

Allows the user to remove a stock from their watchlist.

**Route:** `/delete_stock/<stock_id>`  
**Methods:** `POST`  
**Authentication:** Required  

**URL Parameters:**
- `stock_id` (int) – The ID of the stock to delete.

**Response:**
- Redirects to the watchlist page and flashes success or error messages.

---

Stock Details
~~~~~~~~~~~~~

Displays detailed information about a specific stock.

**Route:** `/stock_details/<stock_id>`  
**Methods:** `GET`  
**Authentication:** Required  

**URL Parameters:**
- `stock_id` (int) – The ID of the stock to fetch details for.

**Response:**
- Renders the `stock/stock_details.html` template with the stock details.

---

Helper Functions
----------------

Get Stock News
~~~~~~~~~~~~~~

Fetches the latest 3 news articles for a given stock.

**Arguments:**
- `symbol` (str): The stock symbol.

**Returns:**
- A list of news articles, each containing:
  - `title` (string)
  - `link` (string)
  - `publishTime` (string)
  - `thumbnail` (string or None)

---

Update Stock Prices
~~~~~~~~~~~~~~~~~~~

Updates stock prices daily and removes stocks that are no longer in any watchlist.

---

Update a Single Stock
~~~~~~~~~~~~~~~~~~~~~

Fetches and updates the latest price for a single stock.

**Arguments:**
- `stock` (Stock): The stock object to update.

---

Get Stock Details
~~~~~~~~~~~~~~~~~

Fetches detailed information about a specific stock using the Yahoo! Finance API.

**Arguments:**
- `symbol` (str): The stock symbol.

**Returns:**
- A JSON string containing stock details such as prices, percent changes, and trading volumes.

---

Generate Daily Report
~~~~~~~~~~~~~~~~~~~~~

Generates a daily report for all stocks in user watchlists and sends the report via email.

**Arguments:**
- `app`: The Flask app context.
