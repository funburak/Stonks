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

Profile
~~~~~~~

Displays the user's profile information.

**Route:** `/profile`
**Methods:** `GET`
**Authentication:** Required

**Features:**
- Lets users view their profile information.
- Lets users update their profile picture, username, email, and notification settings.
- Lets users update their notification settings.
- Lets users delete their account.

- **GET**: Renders the user's profile page (`auth/profile.html`).

---

Upload Profile Picture
~~~~~~~~~~~~~~~~~~~~~~

Allows users to upload a profile picture.

**Route:** `/upload_profile_picture`
**Methods:** `POST`
**Authentication:** Required

- **POST**: Uploads the users selected profile picture to Cloudinary.

---

Toggle Notifications
~~~~~~~~~~~~~~~~~~~~

Allows users to toggle notifications.

**Route:** `/toggle_notifications`
**Methods:** `POST`
**Authentication:** Required

- **POST**: Toggles the users notification settings.

---

Update Username
~~~~~~~~~~~~~~~

Allows users to update their username.

**Route:** `/update_username`
**Methods:** `POST`
**Authentication:** Required

- **POST**: Updates the users username.

---

Update Email
~~~~~~~~~~~~

Allows users to update their email.

**Route:** `/update_email`
**Methods:** `POST`
**Authentication:** Required

- **POST**: Sends a verification email to the new email.

---

Confirm Email Change
~~~~~~~~~~~~~~~~~~~~

Allows users to confirm their email change.

**Route:** `/confirm_email_change/<token>`
**Methods:** `GET`, `POST`
**Authentication:** Required

- **GET**: Renders the email change confirmation page.
- **POST**: Updates the users email.

---

Delete Account
~~~~~~~~~~~~~~

Allows users to delete their account.

**Route:** `/delete_account`
**Methods:** `POST`
**Authentication:** Required

- **POST**: Deletes the users account.

---

Verify OTP
~~~~~~~~~~

Allows users to verify the OTP sent to their email.

**Route:** `/verify_otp`
**Methods:** `POST`

- **POST**: Verifies the OTP.

---

Logout
~~~~~~

Logs out the current user.

**Route:** `/logout`  
**Methods:** `POST`
**Authentication:** Required

**Features:**
- Ends the user session.
- Redirects to the login page.

---

Blueprint Details
-----------------
The `auth` Blueprint is registered in the `stonks.auth` module and contains all the authentication-related functionality.

---

Helper Functions
~~~~~~~~~~~~~~~~

The `auth` Blueprint includes several helper functions to facilitate user authentication and authorization.

- `generate_otp()`: Generates a random OTP for authentication of the user after signup.