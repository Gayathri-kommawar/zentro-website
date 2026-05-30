
from flask import Flask, render_template, request, redirect, session

from flask_dance.contrib.google import make_google_blueprint, google



from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import razorpay
import random
import os


# Flask App
app = Flask(__name__)

app.secret_key = 'secret123'
# ---------------- GOOGLE LOGIN ----------------

blueprint = make_google_blueprint(

    client_id="137397365632-2semg4asg22jlfrlb4vbr4gtfppb5bbr.apps.googleusercontent.com",

    client_secret="5573805937490100689",

    scope=[
        "profile",
        "email"
    ],

    redirect_url="/google-login"
)

app.register_blueprint(
    blueprint,
    url_prefix="/login"
)

# MySQL Configuration


app.config['MYSQL_HOST'] = os.environ.get("MYSQL_HOST")
app.config['MYSQL_USER'] = os.environ.get("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.environ.get("MYSQL_DB")

mysql = MySQL(app)





# ---------------- MAIL CONFIG ----------------

app.config['MAIL_SERVER'] = 'smtp.gmail.com'

app.config['MAIL_PORT'] = 587

app.config['MAIL_USERNAME'] = 'gayathrikommawar7@gmail.com'

app.config['MAIL_PASSWORD'] = 'bgfz djgm ihqq ixqh'

app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

 # ---------------- RAZORPAY ---------------- 
client = razorpay.Client( auth=("YOUR_KEY_ID", "YOUR_SECRET_KEY") )


# ---------------- WELCOME PAGE ----------------

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

# ---------------- USER LOGIN ----------------

@app.route('/')
def login_page():
    return render_template('login.html')

# Signup Page
@app.route('/signup')
def signup_page():
    return render_template('signup.html')

# Register User
@app.route('/register', methods=['POST'])
def register():

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()

    cur.execute(
        "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
        (name, email, password)
    )

    mysql.connection.commit()

    return redirect('/welcome')

# User Login
@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email, password)
    )

    user = cur.fetchone()

    if user:

        session['user'] = user[1]

        return redirect('/dashboard')

    return "Invalid Email or Password"

# ---------------- USER DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM products")

    products = cur.fetchall()

    return render_template(
        'dashboard.html',
        products=products
    )

# Product Details
@app.route('/product/<int:id>')
def product(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM products WHERE id=%s",
        (id,)
    )

    product = cur.fetchone()

    return render_template(
        'product.html',
        product=product
    )

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.pop('user', None)
    session.pop('admin', None)

    return redirect('/welcome')

# ---------------- ADMIN LOGIN ----------------

@app.route('/admin-login')
def admin_login_page():
    return render_template('admin_login.html')

# Admin Login Check
@app.route('/admin-login-user', methods=['POST'])
def admin_login():

    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM admin WHERE email=%s AND password=%s",
        (email, password)
    )

    admin = cur.fetchone()

    if admin:

        session['admin'] = admin[1]

        return redirect('/admin-dashboard')

    return "Invalid Admin Credentials"

# ---------------- ADMIN DASHBOARD ----------------

@app.route('/admin-dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM products")

    products = cur.fetchall()

    return render_template(
        'admin_dashboard.html',
        products=products
    )

# ---------------- ADD PRODUCT ----------------

@app.route('/add-product')
def add_product_page():

    if 'admin' not in session:
        return redirect('/admin-login')

    return render_template('add_product.html')

# Insert Product
@app.route('/insert-product', methods=['POST'])
def insert_product():

    name = request.form['name']
    price = request.form['price']
    image = request.form['image']

    cur = mysql.connection.cursor()

    cur.execute(
        """
        INSERT INTO products(name, price, image)
        VALUES(%s,%s,%s)
        """,
        (name, price, image)
    )

    mysql.connection.commit()

    return redirect('/admin-dashboard')

# Delete Product
@app.route('/delete-product/<int:id>')
def delete_product(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM products WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    return redirect('/admin-dashboard')

# ---------------- SEARCH PRODUCT ----------------

@app.route('/search')
def search():

    keyword = request.args.get('keyword')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM products WHERE name LIKE %s",
        ('%' + keyword + '%',)
    )

    products = cur.fetchall()

    return render_template(
        'dashboard.html',
        products=products
    )

# ---------------- CART SYSTEM ----------------

# Add To Cart
@app.route('/add-to-cart/<int:id>')
def add_to_cart(id):

    cur = mysql.connection.cursor()

    # Check Product Exists
    cur.execute(
        "SELECT * FROM cart WHERE product_id=%s",
        (id,)
    )

    existing = cur.fetchone()

    # Increase Quantity
    if existing:

        cur.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE product_id=%s
            """,
            (id,)
        )

    else:

        # Get Product
        cur.execute(
            "SELECT * FROM products WHERE id=%s",
            (id,)
        )

        product = cur.fetchone()

        # Insert Into Cart
        cur.execute(
            """
            INSERT INTO cart(
                product_id,
                product_name,
                price,
                image,
                quantity
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                product[0],
                product[1],
                product[2],
                product[3],
                1
            )
        )

    mysql.connection.commit()

    return redirect('/cart')

# Cart Page
@app.route('/cart')
def cart():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM cart")

    cart_items = cur.fetchall()

    total = 0

    for item in cart_items:

        total += item[3] * item[5]

    return render_template(
        'cart.html',
        cart_items=cart_items,
        total=total
    )

# Remove Cart Item
@app.route('/remove-cart/<int:id>')
def remove_cart(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM cart WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    return redirect('/cart')

# Increase Quantity
@app.route('/increase-quantity/<int:id>')
def increase_quantity(id):

    cur = mysql.connection.cursor()

    cur.execute(
        """
        UPDATE cart
        SET quantity = quantity + 1
        WHERE id=%s
        """,
        (id,)
    )

    mysql.connection.commit()

    return redirect('/cart')

# Decrease Quantity
@app.route('/decrease-quantity/<int:id>')
def decrease_quantity(id):

    cur = mysql.connection.cursor()

    cur.execute(
        """
        UPDATE cart
        SET quantity = quantity - 1
        WHERE id=%s AND quantity > 1
        """,
        (id,)
    )

    mysql.connection.commit()

    return redirect('/cart')

# ---------------- RUN APP ----------------

# ---------------- CHECKOUT ----------------

@app.route('/checkout')
def checkout():

    cur = mysql.connection.cursor()

    # Get Cart Items
    cur.execute("SELECT * FROM cart")

    cart_items = cur.fetchall()

    # Insert Into Orders
    for item in cart_items:

        total = item[3] * item[5]

        cur.execute(
            """
            INSERT INTO orders(
                product_name,
                price,
                image,
                quantity,
                total
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                item[2],
                item[3],
                item[4],
                item[5],
                total
            )
        )

    # Clear Cart
    cur.execute("DELETE FROM cart")

    mysql.connection.commit()

    return redirect('/payment-success')

# ---------------- ORDERS PAGE ----------------

@app.route('/orders')
def orders():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM orders")

    order_items = cur.fetchall()

    return render_template(
        'orders.html',
        order_items=order_items
    )

# ---------------- RAZORPAY ----------------

import razorpay

client = razorpay.Client(
    auth=(
        "rzp_test_SvEyOrRrLvHSxK",
        "Mqmpg8rlynSGLtB5NVoxscgI"
    )
)

# ---------------- PAYMENT PAGE ----------------

@app.route('/payment')
def payment():

    amount = 50000

    order = client.order.create({

        "amount": amount,

        "currency": "INR",

        "payment_capture": "1"

    })

    return render_template(
        'payment.html',
        payment=order
    )

# ---------------- PAYMENT SUCCESS ----------------

@app.route('/payment-success')
def payment_success():

    return """
    <h1 style='color:green;text-align:center;margin-top:100px;'>
        Payment Successful ✅
    </h1>
    """




# ---------------- BUY NOW ----------------

@app.route('/buy-now/<int:id>')
def buy_now(id):

    cur = mysql.connection.cursor()

    # Get Product
    cur.execute(
        "SELECT * FROM products WHERE id=%s",
        (id,)
    )

    product = cur.fetchone()

    # Clear Old Cart
    cur.execute("DELETE FROM cart")

    # Insert Product Into Cart
    cur.execute(
        """
        INSERT INTO cart(
            product_id,
            product_name,
            price,
            image,
            quantity
        )
        VALUES(%s,%s,%s,%s,%s)
        """,
        (
            product[0],
            product[1],
            product[2],
            product[3],
            1
        )
    )

    mysql.connection.commit()

    return redirect('/checkout')


# ---------------- USER PROFILE ----------------

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/')

    user_name = session['user']

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM users WHERE name=%s",
        (user_name,)
    )

    user = cur.fetchone()

    return render_template(
        'profile.html',
        user=user
    )


# ---------------- WISHLIST ----------------

# Add To Wishlist
@app.route('/add-wishlist/<int:id>')
def add_wishlist(id):

    cur = mysql.connection.cursor()

    # Get Product
    cur.execute(
        "SELECT * FROM products WHERE id=%s",
        (id,)
    )

    product = cur.fetchone()

    # Check Already Exists
    cur.execute(
        "SELECT * FROM wishlist WHERE product_id=%s",
        (id,)
    )

    existing = cur.fetchone()

    if not existing:

        cur.execute(
            """
            INSERT INTO wishlist(
                product_id,
                product_name,
                price,
                image
            )
            VALUES(%s,%s,%s,%s)
            """,
            (
                product[0],
                product[1],
                product[2],
                product[3]
            )
        )

        mysql.connection.commit()

    return redirect('/wishlist')

# Wishlist Page
@app.route('/wishlist')
def wishlist():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM wishlist")

    wishlist_items = cur.fetchall()

    return render_template(
        'wishlist.html',
        wishlist_items=wishlist_items
    )

# Remove Wishlist Item
@app.route('/remove-wishlist/<int:id>')
def remove_wishlist(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM wishlist WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    return redirect('/wishlist')



# ---------------- PLACE ORDER ----------------
@app.route('/place-order')
def place_order():


    cur = mysql.connection.cursor()

    # Get Cart Items
    cur.execute("SELECT * FROM cart")

    cart_items = cur.fetchall()

    # Insert Into Orders
    for item in cart_items:

        total = item[3] * item[5]

        cur.execute(
            """
            INSERT INTO orders(
                product_name,
                price,
                image,
                quantity,
                total
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                item[2],
                item[3],
                item[4],
                item[5],
                total
            )
        )

    # Clear Cart
    cur.execute("DELETE FROM cart")

    mysql.connection.commit()
    # SEND ORDER EMAIL 
    msg = Message( 'Order Confirmed', sender='gayathrikommawar7@gmail.com', 
                  recipients=['gayathrikommawar7@gmail.com'] 
                  ) 
    msg.body = 'Your order has been placed successfully!'
    mail.send(msg)

    return redirect('/payment-success')


# ---------------- TEST EMAIL ----------------

@app.route('/test-email')
def test_email():

    msg = Message(
        'Test Email',
        sender='gayathrikommawar7@gmail.com',
        recipients=['gayathrikommawar7@gmail.com']
    )

    msg.body = 'Flask mail is working successfully.'

    mail.send(msg)

    return "Email Sent Successfully"

# ---------------- OTP LOGIN ----------------

import random

# OTP Login Page
@app.route('/otp-login')
def otp_login():
    return render_template('otp_login.html')

# Send OTP
@app.route('/send-otp', methods=['POST'])
def send_otp():

    email = request.form['email']

    otp = random.randint(1000, 9999)

    session['otp'] = otp
    session['email'] = email

    msg = Message(
        'OTP Verification',
        sender='gayathrikommawar7@gmail.com',
        recipients=[email]
    )

    msg.body = f'Your OTP is {otp}'

    mail.send(msg)

    return render_template('verify_otp.html')

# Verify OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():

    user_otp = request.form['otp']

    if int(user_otp) == session['otp']:

        session['user'] = session['email']

        return redirect('/dashboard')

    return "Invalid OTP"


# ---------------- TRACK ORDERS ----------------

@app.route('/track-orders')
def track_orders():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM orders")

    orders = cur.fetchall()

    return render_template(
        'track_orders.html',
        orders=orders
    )



if __name__ == '__main__':
    app.run(debug=True)

