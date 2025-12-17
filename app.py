from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from models import db, User, Room, Guest, Booking, Payment
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hotel-management-secret-key-2024'


MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''  
MYSQL_DATABASE = 'hotel_management'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_db():
    with app.app_context():
        db.create_all()
        
      
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
        
        if not User.query.filter_by(username='staff').first():
            staff = User(
                username='staff',
                password=generate_password_hash('staff123'),
                role='staff'
            )
            db.session.add(staff)
        
        db.session.commit()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    occupied_rooms = Room.query.filter_by(status='occupied').count()
    total_guests = Guest.query.count()
    active_bookings = Booking.query.filter(Booking.status.in_(['confirmed', 'checked_in'])).count()
    today_checkins = Booking.query.filter(
        Booking.check_in_date == date.today(),
        Booking.status == 'confirmed'
    ).count()
    today_checkouts = Booking.query.filter(
        Booking.check_out_date == date.today(),
        Booking.status == 'checked_in'
    ).count()
    
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    
    return render_template('dashboard.html',
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms,
        total_guests=total_guests,
        active_bookings=active_bookings,
        today_checkins=today_checkins,
        today_checkouts=today_checkouts,
        recent_bookings=recent_bookings
    )


@app.route('/rooms')
@login_required
def rooms():
    all_rooms = Room.query.order_by(Room.room_number).all()
    return render_template('rooms.html', rooms=all_rooms)

@app.route('/rooms/add', methods=['GET', 'POST'])
@login_required
def add_room():
    if current_user.role != 'admin':
        flash('Only admin can add rooms.', 'error')
        return redirect(url_for('rooms'))
    
    if request.method == 'POST':
        room = Room(
            room_number=request.form.get('room_number'),
            room_type=request.form.get('room_type'),
            price_per_night=float(request.form.get('price_per_night')),
            floor=int(request.form.get('floor')),
            capacity=int(request.form.get('capacity')),
            amenities=request.form.get('amenities'),
            status='available'
        )
        
        try:
            db.session.add(room)
            db.session.commit()
            flash('Room added successfully!', 'success')
            return redirect(url_for('rooms'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding room: {str(e)}', 'error')
    
    return render_template('add_room.html')

@app.route('/rooms/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_room(id):
    if current_user.role != 'admin':
        flash('Only admin can edit rooms.', 'error')
        return redirect(url_for('rooms'))
    
    room = Room.query.get_or_404(id)
    
    if request.method == 'POST':
        room.room_number = request.form.get('room_number')
        room.room_type = request.form.get('room_type')
        room.price_per_night = float(request.form.get('price_per_night'))
        room.floor = int(request.form.get('floor'))
        room.capacity = int(request.form.get('capacity'))
        room.amenities = request.form.get('amenities')
        room.status = request.form.get('status')
        
        try:
            db.session.commit()
            flash('Room updated successfully!', 'success')
            return redirect(url_for('rooms'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating room: {str(e)}', 'error')
    
    return render_template('edit_room.html', room=room)

@app.route('/rooms/delete/<int:id>')
@login_required
def delete_room(id):
    if current_user.role != 'admin':
        flash('Only admin can delete rooms.', 'error')
        return redirect(url_for('rooms'))
    
    room = Room.query.get_or_404(id)
    
    try:
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting room: {str(e)}', 'error')
    
    return redirect(url_for('rooms'))


@app.route('/guests')
@login_required
def guests():
    all_guests = Guest.query.order_by(Guest.created_at.desc()).all()
    return render_template('guests.html', guests=all_guests)

@app.route('/guests/add', methods=['GET', 'POST'])
@login_required
def add_guest():
    if request.method == 'POST':
        guest = Guest(
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            id_proof=request.form.get('id_proof')
        )
        
        try:
            db.session.add(guest)
            db.session.commit()
            flash('Guest added successfully!', 'success')
            return redirect(url_for('guests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding guest: {str(e)}', 'error')
    
    return render_template('add_guest.html')

@app.route('/guests/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_guest(id):
    guest = Guest.query.get_or_404(id)
    
    if request.method == 'POST':
        guest.name = request.form.get('name')
        guest.phone = request.form.get('phone')
        guest.email = request.form.get('email')
        guest.address = request.form.get('address')
        guest.id_proof = request.form.get('id_proof')
        
        try:
            db.session.commit()
            flash('Guest updated successfully!', 'success')
            return redirect(url_for('guests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating guest: {str(e)}', 'error')
    
    return render_template('edit_guest.html', guest=guest)

@app.route('/guests/delete/<int:id>')
@login_required
def delete_guest(id):
    guest = Guest.query.get_or_404(id)
    
    try:
        db.session.delete(guest)
        db.session.commit()
        flash('Guest deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting guest: {str(e)}', 'error')
    
    return redirect(url_for('guests'))


@app.route('/bookings')
@login_required
def bookings():
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('bookings.html', bookings=all_bookings)

@app.route('/bookings/add', methods=['GET', 'POST'])
@login_required
def add_booking():
    if request.method == 'POST':
        room_id = int(request.form.get('room_id'))
        guest_id = int(request.form.get('guest_id'))
        check_in_date = datetime.strptime(request.form.get('check_in_date'), '%Y-%m-%d').date()
        check_out_date = datetime.strptime(request.form.get('check_out_date'), '%Y-%m-%d').date()
        
        room = Room.query.get(room_id)
        
        if room.status != 'available':
            flash('This room is not available for booking.', 'error')
            return redirect(url_for('add_booking'))
        
        nights = (check_out_date - check_in_date).days
        total_amount = nights * room.price_per_night
        
        booking = Booking(
            room_id=room_id,
            guest_id=guest_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_amount=total_amount,
            special_requests=request.form.get('special_requests'),
            status='confirmed'
        )
        
        room.status = 'booked'
        
        try:
            db.session.add(booking)
            db.session.commit()
            flash('Booking created successfully!', 'success')
            return redirect(url_for('bookings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating booking: {str(e)}', 'error')
    
    available_rooms = Room.query.filter_by(status='available').all()
    all_guests = Guest.query.all()
    return render_template('add_booking.html', rooms=available_rooms, guests=all_guests)

@app.route('/bookings/view/<int:id>')
@login_required
def view_booking(id):
    booking = Booking.query.get_or_404(id)
    return render_template('view_booking.html', booking=booking)

@app.route('/bookings/cancel/<int:id>')
@login_required
def cancel_booking(id):
    booking = Booking.query.get_or_404(id)
    
    if booking.status in ['checked_in', 'checked_out']:
        flash('Cannot cancel a booking that has already been checked in or out.', 'error')
        return redirect(url_for('bookings'))
    
    booking.status = 'cancelled'
    booking.room.status = 'available'
    
    try:
        db.session.commit()
        flash('Booking cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling booking: {str(e)}', 'error')
    
    return redirect(url_for('bookings'))


@app.route('/checkin/<int:booking_id>')
@login_required
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status != 'confirmed':
        flash('This booking cannot be checked in.', 'error')
        return redirect(url_for('bookings'))
    
    booking.status = 'checked_in'
    booking.checked_in_at = datetime.utcnow()
    booking.room.status = 'occupied'
    
    try:
        db.session.commit()
        flash('Guest checked in successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during check-in: {str(e)}', 'error')
    
    return redirect(url_for('bookings'))

@app.route('/checkout/<int:booking_id>')
@login_required
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status != 'checked_in':
        flash('This booking cannot be checked out.', 'error')
        return redirect(url_for('bookings'))
    
    booking.status = 'checked_out'
    booking.checked_out_at = datetime.utcnow()
    booking.room.status = 'available'
    
    try:
        db.session.commit()
        flash('Guest checked out successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during check-out: {str(e)}', 'error')
    
    return redirect(url_for('bookings'))


@app.route('/payments')
@login_required
def payments():
    all_payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return render_template('payments.html', payments=all_payments)

@app.route('/payments/add/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def add_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        payment = Payment(
            booking_id=booking_id,
            amount=float(request.form.get('amount')),
            payment_method=request.form.get('payment_method'),
            payment_status=request.form.get('payment_status'),
            transaction_id=request.form.get('transaction_id'),
            notes=request.form.get('notes')
        )
        
        try:
            db.session.add(payment)
            db.session.commit()
            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('view_booking', id=booking_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'error')
    
    return render_template('add_payment.html', booking=booking)


@app.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('add_user'))
        
        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('add_user.html')

@app.route('/users/delete/<int:id>')
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    if current_user.id == id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('users'))
    
    user = User.query.get_or_404(id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('users'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5200)

