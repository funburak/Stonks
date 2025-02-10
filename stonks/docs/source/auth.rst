Auth Blueprint
==============

The `auth` Blueprint handles authentication-related routes, including user signup, login, password recovery, and logout.

.. automodule:: auth
   :members:
   :undoc-members:
   :show-inheritance:

Routes
------

Signup
~~~~~~

Handles user registration. If the user is already logged in, they are redirected to the homepage.

**Route:** `/signup`  
**Methods:** `GET`, `POST`  

- **GET**: Renders the signup form (`auth/signup.html`).
- **POST**: Processes the signup form, validates input, and creates a new user.

**Features:**
- Ensures email and username are unique.
- Hashes the password before storing it.
- Automatically redirects the user to the login page after successful signup.

---

Login
~~~~~

Handles user login. If the user is already logged in, they are redirected to the homepage.

**Route:** `/login`  
**Methods:** `GET`, `POST`  

- **GET**: Renders the login form (`auth/login.html`).
- **POST**: Authenticates the user based on the provided username and password.

**Features:**
- Autofills the username if the user has just signed up.
- Redirects to the dashboard upon successful login.

---

Forgot Password
~~~~~~~~~~~~~~~

Allows users to request a password reset email.

**Route:** `/forgot_password`  
**Methods:** `GET`, `POST`  

- **GET**: Renders the forgot password form (`auth/forgot_password.html`).
- **POST**: Sends a password reset email if the provided email is registered.

**Features:**
- Generates a reset token.
- Sends a password reset email with a token-based link.

---

Reset Password
~~~~~~~~~~~~~~

Handles password reset requests using a token.

**Route:** `/reset_password/<token>`  
**Methods:** `GET`, `POST`  

- **GET**: Renders the password reset form (`auth/reset_password.html`).
- **POST**: Updates the user's password if the token is valid.

**Features:**
- Validates the reset token.
- Ensures the new password and confirmation password match.

---

Logout
~~~~~~

Logs out the current user.

**Route:** `/logout`  
**Methods:** `POST`  

**Features:**
- Ends the user session.
- Redirects to the login page.

---

Blueprint Details
-----------------
The `auth` Blueprint is registered in the `stonks.auth` module and contains all the authentication-related functionality.

