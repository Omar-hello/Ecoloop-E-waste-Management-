"""
EcoLoop — E-Waste Recycling & Collection Management System
Flask Backend — Production Ready
Works on: localhost, Railway.app, Render.com, PythonAnywhere

COURSE: CSTE2201 — Database Management System
AUTHORS: Rashedul Alam Noyon (ASH2201041M)
         Khan Md. Omar Faruqe (ASH2301022M)

HOW TO RUN LOCALLY:
  1. pip install -r requirements.txt
  2. python app.py
  3. Open http://localhost:5000

HOW TO DEPLOY (Railway/Render):
  - Push to GitHub, connect repo, Railway auto-detects Flask
  - Set DATABASE_URL environment variable (Railway does this automatically)
"""

import os
import bcrypt
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# ─── APP SETUP ────────────────────────────────────────────────────
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ─── DATABASE CONFIG ──────────────────────────────────────────────
# Reads DATABASE_URL from environment (set automatically by Railway/Render)
# Falls back to local SQLite for development
database_url = os.environ.get('DATABASE_URL', 'sqlite:///ewaste.db')

# Fix: Railway uses 'postgres://' but SQLAlchemy needs 'postgresql://'
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ecoloop-dev-secret-change-in-prod-2025')

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────

class Admin(db.Model):
    __tablename__ = 'admins'
    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(50), unique=True, nullable=False)
    email     = db.Column(db.String(100), unique=True, nullable=False)
    password  = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), default='Admin')
    created   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'role': 'admin', 'email': self.email,
                'firstName': self.full_name, 'lastName': '', 'username': self.username}


class Donor(db.Model):
    __tablename__ = 'donors'
    id            = db.Column(db.Integer, primary_key=True)
    first_name    = db.Column(db.String(50), nullable=False)
    last_name     = db.Column(db.String(50), default='')
    email         = db.Column(db.String(100), unique=True, nullable=False)
    phone         = db.Column(db.String(20), default='')
    address       = db.Column(db.Text, default='')
    password_hash = db.Column(db.String(255))
    google_id     = db.Column(db.String(150), unique=True)
    auth_provider = db.Column(db.String(20), default='local')
    is_active     = db.Column(db.Boolean, default=True)
    reg_date      = db.Column(db.DateTime, default=datetime.utcnow)
    items         = db.relationship('EWasteItem', backref='donor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'role': 'donor',
            'firstName': self.first_name, 'lastName': self.last_name,
            'email': self.email, 'phone': self.phone, 'address': self.address,
            'regDate': self.reg_date.isoformat(), 'authProvider': self.auth_provider
        }


class CollectionCenter(db.Model):
    __tablename__ = 'collection_centers'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    location     = db.Column(db.String(200))
    contact_info = db.Column(db.String(100))
    capacity     = db.Column(db.Integer, default=1000)
    is_active    = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'location': self.location,
                'contactInfo': self.contact_info, 'capacity': self.capacity}


class Recycler(db.Model):
    __tablename__ = 'recyclers'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    contact_info   = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    capacity       = db.Column(db.Integer, default=500)
    is_active      = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'specialization': self.specialization,
                'capacity': self.capacity}


class Product(db.Model):
    __tablename__ = 'products'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    category    = db.Column(db.String(50))
    emoji       = db.Column(db.String(10))
    description = db.Column(db.Text)
    min_price   = db.Column(db.Float, default=0)
    max_price   = db.Column(db.Float, default=0)
    condition   = db.Column(db.String(20), default='Any')
    is_active   = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'category': self.category,
            'emoji': self.emoji, 'desc': self.description,
            'price': f'৳{int(self.min_price):,} – ৳{int(self.max_price):,}',
            'minPrice': self.min_price, 'maxPrice': self.max_price,
            'condition': self.condition
        }


class EWasteItem(db.Model):
    __tablename__ = 'ewaste_items'
    id              = db.Column(db.Integer, primary_key=True)
    donor_id        = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    item_name       = db.Column(db.String(150), nullable=False)
    category        = db.Column(db.String(50))
    description     = db.Column(db.Text, default='')
    condition       = db.Column(db.String(20))
    quantity        = db.Column(db.Integer, default=1)
    submission_date = db.Column(db.Date, default=datetime.utcnow)
    status          = db.Column(db.String(20), default='Pending')
    center_id       = db.Column(db.Integer, db.ForeignKey('collection_centers.id'))
    estimated_price = db.Column(db.Float)
    final_price     = db.Column(db.Float)
    center          = db.relationship('CollectionCenter', backref='items')

    def to_dict(self):
        return {
            'id': self.id, 'donorId': self.donor_id,
            'donorName': f'{self.donor.first_name} {self.donor.last_name}'.strip(),
            'name': self.item_name, 'category': self.category,
            'description': self.description, 'condition': self.condition,
            'quantity': self.quantity, 'date': str(self.submission_date),
            'status': self.status,
            'centerName': self.center.name if self.center else '—',
            'estimatedPrice': self.estimated_price, 'finalPrice': self.final_price
        }


class Collection(db.Model):
    __tablename__ = 'collections'
    id              = db.Column(db.Integer, primary_key=True)
    item_id         = db.Column(db.Integer, db.ForeignKey('ewaste_items.id'), unique=True)
    center_id       = db.Column(db.Integer, db.ForeignKey('collection_centers.id'))
    collection_date = db.Column(db.Date)
    status          = db.Column(db.String(20), default='Scheduled')
    notes           = db.Column(db.Text)


class RecyclingProcess(db.Model):
    __tablename__ = 'recycling_processes'
    id           = db.Column(db.Integer, primary_key=True)
    item_id      = db.Column(db.Integer, db.ForeignKey('ewaste_items.id'))
    recycler_id  = db.Column(db.Integer, db.ForeignKey('recyclers.id'))
    process_type = db.Column(db.String(50))
    process_date = db.Column(db.Date)
    status       = db.Column(db.String(20), default='In Progress')
    notes        = db.Column(db.Text)
    recycler     = db.relationship('Recycler', backref='processes')
    item         = db.relationship('EWasteItem', backref='processes')


class Message(db.Model):
    __tablename__ = 'messages'
    id            = db.Column(db.Integer, primary_key=True)
    from_id       = db.Column(db.Integer, nullable=False)
    from_name     = db.Column(db.String(100))
    from_role     = db.Column(db.String(20))   # 'admin' or 'donor'
    to_id         = db.Column(db.Integer, nullable=False)
    to_name       = db.Column(db.String(100))
    to_role       = db.Column(db.String(20))
    text          = db.Column(db.Text, nullable=False)
    is_read       = db.Column(db.Boolean, default=False)
    sent_at       = db.Column(db.DateTime, default=datetime.utcnow)
    related_item  = db.Column(db.Integer)      # optional: link to item

    def to_dict(self):
        return {
            'id': self.id, 'fromId': self.from_id, 'fromName': self.from_name,
            'fromRole': self.from_role, 'toId': self.to_id, 'toName': self.to_name,
            'toRole': self.to_role, 'text': self.text, 'read': self.is_read,
            'time': self.sent_at.strftime('%Y-%m-%d %H:%M'),
            'relatedItem': self.related_item
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, nullable=False)
    user_role  = db.Column(db.String(20))
    title      = db.Column(db.String(200))
    body       = db.Column(db.Text)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'body': self.body,
                'read': self.is_read, 'time': self.created_at.strftime('%Y-%m-%d %H:%M')}

# ─── AUTH ROUTES ──────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
# def api_register():
#     d = request.get_json()
#     if not d:
#         return jsonify({'error': 'No data provided'}), 400
#     if Donor.query.filter_by(email=d.get('email','')).first():
#         return jsonify({'error': 'Email already registered'}), 400

#     pw = d.get('password', '')
#     if len(pw) < 6:
#         return jsonify({'error': 'Password must be at least 6 characters'}), 400

#     pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
#     donor = Donor(
#         first_name=d.get('firstName',''), last_name=d.get('lastName',''),
#         email=d['email'], phone=d.get('phone',''),
#         address=d.get('address',''), password_hash=pw_hash
#     )
#     db.session.add(donor)

#     # Welcome notification
#     notif = Notification(user_id=donor.id, user_role='donor',
#                          title='Welcome to EcoLoop! 🌿',
#                          body='Your account is ready. Submit your first e-waste item to get started!')
#     db.session.add(notif)
#     db.session.commit()

#     return jsonify({'success': True, 'user': donor.to_dict()})
def api_register():
    d = request.get_json()
    if not d:
        return jsonify({'error': 'No data provided'}), 400
    if Donor.query.filter_by(email=d.get('email','')).first():
        return jsonify({'error': 'Email already registered'}), 400

    pw = d.get('password', '')
    if len(pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    donor = Donor(
        first_name=d.get('firstName',''), last_name=d.get('lastName',''),
        email=d['email'], phone=d.get('phone',''),
        address=d.get('address',''), password_hash=pw_hash
    )
    db.session.add(donor)
    db.session.commit()  # <-- ONLY THIS LINE (no flush, no notification)

    return jsonify({'success': True, 'user': donor.to_dict()})

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json()
    if not d:
        return jsonify({'error': 'No data'}), 400

    role = d.get('role', 'donor')
    email = d.get('email', '').strip().lower()
    pw = d.get('password', '')

    if role == 'admin':
        admin = Admin.query.filter_by(email=email).first()
        if admin and bcrypt.checkpw(pw.encode(), admin.password.encode()):
            return jsonify({'success': True, 'user': admin.to_dict()})
        return jsonify({'error': 'Invalid admin credentials'}), 401

    donor = Donor.query.filter_by(email=email, is_active=True).first()
    if donor and donor.password_hash and bcrypt.checkpw(pw.encode(), donor.password_hash.encode()):
        return jsonify({'success': True, 'user': donor.to_dict()})
    return jsonify({'error': 'Invalid email or password'}), 401


@app.route('/api/google-login', methods=['POST'])
def api_google_login():
    """
    In production: verify Google ID token using google-auth library.
    For demo: auto-register with Google profile info.
    """
    d = request.get_json()
    if not d:
        return jsonify({'error': 'No data'}), 400

    google_id = d.get('googleId', '')
    email = d.get('email', '')
    name_parts = d.get('name', 'Google User').split(' ', 1)
    first = name_parts[0]
    last = name_parts[1] if len(name_parts) > 1 else ''

    # Check by Google ID first
    existing = Donor.query.filter_by(google_id=google_id).first() if google_id else None
    # Then check by email
    if not existing and email:
        existing = Donor.query.filter_by(email=email).first()

    if existing:
        if google_id and not existing.google_id:
            existing.google_id = google_id
            db.session.commit()
        return jsonify({'success': True, 'user': existing.to_dict()})

    # Auto-register
    donor = Donor(first_name=first, last_name=last, email=email,
                  google_id=google_id, auth_provider='google')
    db.session.add(donor)
    db.session.commit()
    return jsonify({'success': True, 'user': donor.to_dict()})

# ─── USER ROUTES ──────────────────────────────────────────────────

@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = Donor.query.filter_by(is_active=True).order_by(Donor.reg_date.desc()).all()
    return jsonify([u.to_dict() for u in users])


@app.route('/api/users/<int:uid>', methods=['PATCH'])
def api_update_user(uid):
    donor = Donor.query.get_or_404(uid)
    d = request.get_json()
    if 'firstName' in d: donor.first_name = d['firstName']
    if 'lastName'  in d: donor.last_name  = d['lastName']
    if 'phone'     in d: donor.phone      = d['phone']
    if 'address'   in d: donor.address    = d['address']
    db.session.commit()
    return jsonify(donor.to_dict())


@app.route('/api/users/<int:uid>', methods=['DELETE'])
def api_delete_user(uid):
    donor = Donor.query.get_or_404(uid)
    donor.is_active = False
    db.session.commit()
    return jsonify({'success': True})

# ─── PRODUCTS ROUTES ──────────────────────────────────────────────

@app.route('/api/products', methods=['GET'])
def api_get_products():
    cat = request.args.get('category', '')
    q = Product.query.filter_by(is_active=True)
    if cat:
        q = q.filter_by(category=cat)
    return jsonify([p.to_dict() for p in q.order_by(Product.category).all()])


@app.route('/api/products', methods=['POST'])
def api_add_product():
    d = request.get_json()
    p = Product(
        name=d['name'], category=d.get('category','Other'),
        emoji=d.get('emoji','📦'), description=d.get('description',''),
        min_price=d.get('minPrice',0), max_price=d.get('maxPrice',0),
        condition=d.get('condition','Any')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict())


@app.route('/api/products/<int:pid>', methods=['PATCH'])
def api_update_product(pid):
    p = Product.query.get_or_404(pid)
    d = request.get_json()
    for field in ['name','category','emoji','description','condition']:
        if field in d: setattr(p, field, d[field])
    if 'minPrice' in d: p.min_price = d['minPrice']
    if 'maxPrice' in d: p.max_price = d['maxPrice']
    db.session.commit()
    return jsonify(p.to_dict())


@app.route('/api/products/<int:pid>', methods=['DELETE'])
def api_delete_product(pid):
    p = Product.query.get_or_404(pid)
    p.is_active = False
    db.session.commit()
    return jsonify({'success': True})

# ─── SUBMISSIONS ROUTES ───────────────────────────────────────────

@app.route('/api/submissions', methods=['GET'])
def api_get_submissions():
    donor_id = request.args.get('donorId')
    status   = request.args.get('status')
    q = EWasteItem.query
    if donor_id: q = q.filter_by(donor_id=int(donor_id))
    if status:   q = q.filter_by(status=status)
    items = q.order_by(EWasteItem.submission_date.desc()).all()
    return jsonify([i.to_dict() for i in items])


@app.route('/api/submissions', methods=['POST'])
def api_add_submission():
    d = request.get_json()
    if not d or not d.get('donorId') or not d.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400

    item = EWasteItem(
        donor_id=d['donorId'], item_name=d['name'],
        category=d.get('category','Other'), description=d.get('description',''),
        condition=d.get('condition','Fair'), quantity=d.get('quantity',1),
        submission_date=datetime.utcnow().date(),
        center_id=d.get('centerId') or None
    )
    db.session.add(item)
    db.session.flush()  # get item.id

    # Create collection record if center chosen
    if item.center_id:
        coll = Collection(item_id=item.id, center_id=item.center_id)
        db.session.add(coll)

    # Notify admin
    notif = Notification(user_id=1, user_role='admin',
        title=f'New Submission: {item.item_name}',
        body=f'{item.donor.first_name} submitted {item.item_name} ({item.category})')
    db.session.add(notif)
    db.session.commit()

    return jsonify({'success': True, 'submission': item.to_dict()})


@app.route('/api/submissions/<int:sid>', methods=['PATCH'])
def api_update_submission(sid):
    item = EWasteItem.query.get_or_404(sid)
    d = request.get_json()
    if 'status'         in d: item.status          = d['status']
    if 'estimatedPrice' in d: item.estimated_price  = d['estimatedPrice']
    if 'finalPrice'     in d: item.final_price       = d['finalPrice']
    if 'centerId'       in d: item.center_id         = d['centerId']

    # Notify donor of status change
    if 'status' in d:
        notif = Notification(user_id=item.donor_id, user_role='donor',
            title=f'Item Status Updated: {item.item_name}',
            body=f'Your item "{item.item_name}" status changed to {d["status"]}')
        db.session.add(notif)

    db.session.commit()
    return jsonify({'success': True, 'submission': item.to_dict()})

# ─── MESSAGES ROUTES ──────────────────────────────────────────────

@app.route('/api/messages', methods=['GET'])
def api_get_messages():
    uid1 = request.args.get('userId1')
    uid2 = request.args.get('userId2')
    if uid1 and uid2:
        msgs = Message.query.filter(
            db.or_(
                db.and_(Message.from_id == uid1, Message.to_id == uid2),
                db.and_(Message.from_id == uid2, Message.to_id == uid1)
            )
        ).order_by(Message.sent_at).all()
    else:
        # Admin: get all messages
        msgs = Message.query.order_by(Message.sent_at.desc()).limit(100).all()
    return jsonify([m.to_dict() for m in msgs])


@app.route('/api/messages', methods=['POST'])
def api_send_message():
    d = request.get_json()
    if not d or not d.get('text','').strip():
        return jsonify({'error': 'Empty message'}), 400

    msg = Message(
        from_id=d['fromId'], from_name=d['fromName'], from_role=d['fromRole'],
        to_id=d['toId'], to_name=d['toName'], to_role=d['toRole'],
        text=d['text'].strip(), related_item=d.get('relatedItem')
    )
    db.session.add(msg)

    # Notification for receiver
    notif = Notification(user_id=d['toId'], user_role=d['toRole'],
        title=f'New message from {d["fromName"]}',
        body=d['text'][:80])
    db.session.add(notif)
    db.session.commit()

    return jsonify({'success': True, 'message': msg.to_dict()})


@app.route('/api/messages/mark-read', methods=['POST'])
def api_mark_read():
    d = request.get_json()
    Message.query.filter_by(
        to_id=d['toId'], from_id=d['fromId'], is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

# ─── NOTIFICATIONS ROUTES ─────────────────────────────────────────

@app.route('/api/notifications/<int:uid>', methods=['GET'])
def api_get_notifications(uid):
    notifs = Notification.query.filter_by(user_id=uid, is_read=False)\
        .order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([n.to_dict() for n in notifs])


@app.route('/api/notifications/<int:nid>/read', methods=['POST'])
def api_read_notification(nid):
    n = Notification.query.get_or_404(nid)
    n.is_read = True
    db.session.commit()
    return jsonify({'success': True})

# ─── REPORTS ROUTES ───────────────────────────────────────────────

@app.route('/api/reports/summary', methods=['GET'])
def api_summary():
    total_donors   = Donor.query.filter_by(is_active=True).count()
    total_items    = EWasteItem.query.count()
    recycled       = EWasteItem.query.filter_by(status='Recycled').count()
    pending        = EWasteItem.query.filter_by(status='Pending').count()
    collected      = EWasteItem.query.filter_by(status='Collected').count()
    total_centers  = CollectionCenter.query.filter_by(is_active=True).count()
    total_recyclers= Recycler.query.filter_by(is_active=True).count()
    unread_msgs    = Message.query.filter_by(to_id=1, is_read=False).count()
    return jsonify({
        'donors': total_donors, 'totalItems': total_items,
        'recycled': recycled, 'pending': pending, 'collected': collected,
        'centers': total_centers, 'recyclers': total_recyclers,
        'unreadMessages': unread_msgs
    })


@app.route('/api/reports/categories', methods=['GET'])
def api_categories():
    from sqlalchemy import func
    results = db.session.query(
        EWasteItem.category, func.count(EWasteItem.id).label('count')
    ).group_by(EWasteItem.category).order_by(func.count(EWasteItem.id).desc()).all()
    return jsonify([{'category': r[0], 'count': r[1]} for r in results])


@app.route('/api/reports/monthly', methods=['GET'])
def api_monthly():
    from sqlalchemy import func, extract
    results = db.session.query(
        extract('year',  EWasteItem.submission_date).label('year'),
        extract('month', EWasteItem.submission_date).label('month'),
        func.count(EWasteItem.id).label('total')
    ).group_by('year','month').order_by('year','month').all()
    return jsonify([{'year': int(r[0]), 'month': int(r[1]), 'total': r[2]} for r in results])

# ─── COLLECTION CENTERS ───────────────────────────────────────────

@app.route('/api/centers', methods=['GET'])
def api_get_centers():
    centers = CollectionCenter.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in centers])

# ─── SERVE FRONTEND ───────────────────────────────────────────────

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('.', path)
    except:
        return send_from_directory('.', 'index.html')

# ─── DATABASE SEED ────────────────────────────────────────────────

def seed():
    """Populate database with initial data if empty."""

    # Admin account
    if not Admin.query.first():
        pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        db.session.add(Admin(username='admin', email='admin@ecoloop.com',
                             password=pw, full_name='EcoLoop Admin'))
        print('✅ Admin created: admin@ecoloop.com / admin123')

    # Demo donors
    if Donor.query.count() == 0:
        donors = [
            ('Rashedul','Noyon','rashedul@gmail.com','+880 17 1234 5678','Mirpur, Dhaka','pass123'),
            ('Omar','Faruqe','omar@gmail.com','+880 18 9876 5432','Gulshan, Dhaka','pass123'),
            ('Fatima','Begum','fatima@gmail.com','+880 19 1111 2222','Uttara, Dhaka','pass123'),
        ]
        for fn,ln,em,ph,addr,pw in donors:
            pwhash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            db.session.add(Donor(first_name=fn,last_name=ln,email=em,
                                 phone=ph,address=addr,password_hash=pwhash))
        db.session.flush()
        print('✅ Demo donors created')

    # Collection centers
    if CollectionCenter.query.count() == 0:
        centers = [
            ('Dhaka Central Collection Center','Mirpur-10, Dhaka','01700-000001',2000),
            ('Gulshan E-Waste Hub','Gulshan-2, Dhaka','01700-000002',1500),
            ('Uttara Green Point','Uttara Sector 10, Dhaka','01700-000003',1000),
            ('Motijheel Drop Zone','Motijheel, Dhaka','01700-000004',800),
            ('Chittagong Eco Center','GEC Circle, Chittagong','01700-000005',1200),
        ]
        for name,loc,contact,cap in centers:
            db.session.add(CollectionCenter(name=name,location=loc,
                                            contact_info=contact,capacity=cap))
        print('✅ Collection centers created')

    # Recyclers
    if Recycler.query.count() == 0:
        recyclers = [
            ('GreenTech Recyclers Ltd','01800-111111','Mobile Phones, Tablets',500),
            ('Bangladesh Metal Recovery','01800-222222','Batteries, Metal',800),
            ('EcoCycle BD','01800-333333','Laptops, Desktops',600),
            ('CleanElec Solutions','01800-444444','Appliances, TVs',700),
        ]
        for name,contact,spec,cap in recyclers:
            db.session.add(Recycler(name=name,contact_info=contact,
                                    specialization=spec,capacity=cap))
        print('✅ Recyclers created')

    # Products catalog
    if Product.query.count() == 0:
        products = [
            ('Smartphone (Any Brand)','Mobile','📱','Used or broken mobile phones. All brands accepted.',200,2500,'Any'),
            ('Laptop / Notebook','Laptop','💻','Old laptops, netbooks. Working or non-working.',500,8000,'Good'),
            ('LCD / LED Monitor','TV','🖥️','Flat screen monitors from 15" to 32".',300,3000,'Fair'),
            ('CRT Television','TV','📺','Old tube TVs. Free pickup for large units.',100,500,'Poor'),
            ('Lithium Batteries','Battery','🔋','Li-ion, Li-Po, phone batteries. Safe disposal.',50,300,'Any'),
            ('Lead Acid Battery','Battery','⚡','Car, IPS, motorcycle batteries.',200,1500,'Any'),
            ('Inkjet / Laser Printer','Printer','🖨️','Desktop printers of any size or brand.',150,2000,'Fair'),
            ('Digital Camera','Camera','📷','Point & shoot, DSLR, action cameras.',500,5000,'Good'),
            ('Refrigerator / Fridge','Appliance','🧊','Single/double door fridges. Free pickup.',1000,6000,'Fair'),
            ('Washing Machine','Appliance','🫧','Top or front loading, any condition.',800,4000,'Fair'),
            ('Air Conditioner','Appliance','❄️','Window or split AC units, any brand.',1500,10000,'Good'),
            ('Desktop Computer (Full Set)','Laptop','🖥️','CPU + monitor + keyboard + mouse set.',500,5000,'Fair'),
            ('Router / Modem','Mobile','📡','WiFi routers, DSL modems, hubs.',50,300,'Any'),
            ('Gaming Console','Gaming','🎮','PlayStation, Xbox, Nintendo — all generations.',1000,15000,'Good'),
            ('Power Bank','Battery','🔌','External battery packs, any capacity.',100,800,'Fair'),
            ('Microwave Oven','Appliance','🍽️','All sizes, broken or not.',300,2000,'Fair'),
            ('Electric Fan','Appliance','💨','Table, ceiling, or stand fans.',80,500,'Any'),
            ('Tablet / iPad','Mobile','📟','Android tablets, iPads of any generation.',300,5000,'Good'),
            ('Smart Watch','Mobile','⌚','Fitness bands, smartwatches, any brand.',200,3000,'Good'),
            ('Keyboard & Mouse','Laptop','⌨️','Wired or wireless, gaming or office.',50,400,'Any'),
        ]
        for name,cat,emoji,desc,minp,maxp,cond in products:
            db.session.add(Product(name=name,category=cat,emoji=emoji,
                                   description=desc,min_price=minp,
                                   max_price=maxp,condition=cond))
        print('✅ Products created')

    # Sample items
    if EWasteItem.query.count() == 0:
        d1 = Donor.query.filter_by(email='rashedul@gmail.com').first()
        d2 = Donor.query.filter_by(email='omar@gmail.com').first()
        if d1 and d2:
            items = [
                EWasteItem(donor_id=d1.id,item_name='iPhone 8',category='Mobile',
                           condition='Good',description='Screen cracked, battery OK',
                           quantity=1,submission_date=datetime(2025,1,15).date(),
                           status='Collected',center_id=1),
                EWasteItem(donor_id=d2.id,item_name='Dell Inspiron 15',category='Laptop',
                           condition='Fair',description='Slow, old model',
                           quantity=1,submission_date=datetime(2025,1,20).date(),
                           status='Pending',center_id=None),
                EWasteItem(donor_id=d1.id,item_name='AA Battery Pack x20',category='Battery',
                           condition='Poor',description='Expired batteries',
                           quantity=20,submission_date=datetime(2025,2,1).date(),
                           status='Recycled',center_id=2),
            ]
            for item in items: db.session.add(item)
        print('✅ Sample submissions created')

    # Sample messages
    if Message.query.count() == 0:
        d1 = Donor.query.filter_by(email='rashedul@gmail.com').first()
        admin = Admin.query.first()
        if d1 and admin:
            msgs = [
                Message(from_id=d1.id,from_name='Rashedul',from_role='donor',
                        to_id=admin.id,to_name='Admin',to_role='admin',
                        text='Hello! I submitted an iPhone 8. What is the current price?',is_read=True),
                Message(from_id=admin.id,from_name='Admin',from_role='admin',
                        to_id=d1.id,to_name='Rashedul',to_role='donor',
                        text='Hi Rashedul! For iPhone 8 in Good condition, we offer ৳800–1200. Can you confirm the IMEI?',is_read=True),
                Message(from_id=d1.id,from_name='Rashedul',from_role='donor',
                        to_id=admin.id,to_name='Admin',to_role='admin',
                        text='IMEI: 352099001761481. Please confirm pickup schedule.',is_read=False),
            ]
            for m in msgs: db.session.add(m)
        print('✅ Sample messages created')

    db.session.commit()
    print('\n🌿 EcoLoop database ready!\n')

# ─── ENTRY POINT ──────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed()

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'

    print(f'\n🌿 EcoLoop running at: http://localhost:{port}')
    print('─' * 40)
    print('Admin:  admin@ecoloop.com  /  admin123')
    print('Donor:  rashedul@gmail.com /  pass123')
    print('Donor:  omar@gmail.com     /  pass123')
    print('─' * 40 + '\n')

    app.run(debug=debug, host='0.0.0.0', port=port)
