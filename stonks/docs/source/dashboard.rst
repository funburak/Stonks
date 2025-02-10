Dashboard Blueprint
===================

The `dashboard` Blueprint handles the homepage of the application and provides stock-related updates for logged-in users.

.. automodule:: stonks.dashboard
   :members:
   :undoc-members:
   :show-inheritance:

Routes
------

Homepage
~~~~~~~~


Serves as the main entry point for the application.

**Route:** `/`  
**Methods:** `GET`  
**Authentication:** Optional  

### Behavior:
- **Authenticated Users:**
  - Displays the latest stock news for stocks in the user's watchlist.
  - Fetches stock news using the `get_stock_news` helper function from the `stock` Blueprint.

- **Unauthenticated Users:**
  - Renders the homepage without any stock news.

**Response:**
- Renders the `homepage.html` template.
- For authenticated users, the template includes stock news organized by stock symbol.

---

Blueprint Details
-----------------
The `dashboard` Blueprint is registered in the `stonks.dashboard` module and provides the application's homepage functionality.

---

Helper Functions
----------------
This Blueprint uses the `get_stock_news` function from the `stock` Blueprint to fetch stock-related news.

