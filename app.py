from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from uuid import uuid4
from supabase import create_client, Client
from config import Config


# FIX 1: Removed the redundant client initialization. This is the single source of truth.
supabase_url = Config.SUPABASE_URL
supabase_key = Config.SUPABASE_KEY
supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)
app.config.from_object(Config)
# FIX 2: Use the correct key 'SECRET_KEY' for Flask's secret key.
app.secret_key = app.config['SECRET_KEY']




def fetch_posts():
    """Fetches all resources and their latest status to display as posts."""
    try:
        resources_response = supabase.table('resources').select("*").execute()
        resources = resources_response.data

        posts = []
        for resource in resources:
           
            status_response = supabase.table('status_updates').select("*").eq('resource_id', resource['id']).order('created_at', desc=True).limit(1).execute()
            status = status_response.data[0] if status_response.data else None

        
            upvotes_response = supabase.table('upvotes').select('id', count='exact').eq('resource_id', resource['id']).execute()
            upvotes_count = upvotes_response.count if hasattr(upvotes_response, 'count') else 0

            post = {
                'id': resource['id'],
                'title': resource['name'],
                'image_url': resource['image_url'],
                'description': status['status_message'] if status else 'No status updates yet.',
                'upvotes': upvotes_count,
                'comments': 0,  
                'crowd': status['crowd_level'] if status else 'N/A',
                'chips': status['chips_available'] if status else 'N/A',
                'queue': status['queue_length'] if status else 'N/A'
            }
            posts.append(post)
        
    
        posts.sort(key=lambda x: x['upvotes'], reverse=True)
        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []



def login_required(f):
    """Decorator to ensure a user is logged in."""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    """Decorator to ensure a user is an admin."""
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            # FIX 3: Corrected redirect from 'indexed' to 'index'.
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function



@app.route('/')
def index():
    posts = fetch_posts()
    return render_template('index.html', posts=posts, username=session.get('username'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=session.get('username'))

@app.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username'] 
        password = request.form['password']
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if auth_response.user:
                session['username'] = auth_response.user.email
                session['user_id'] = auth_response.user.id
                
                # FIX 4: Removed hardcoded admin status.
               
                
                return redirect(url_for('profile'))
        except Exception as e:
           
            return render_template('login.html', error="Invalid credentials. Please try again.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['username'] 
        password = request.form['password']
        try:
            auth_response = supabase.auth.sign_up({"email": email, "password": password})
            if auth_response.user:
                
                session['username'] = auth_response.user.email
                session['user_id'] = auth_response.user.id
                session['is_admin'] = False # New users are not admins
        
                return redirect(url_for('profile'))
        except Exception as e:
            return render_template('register.html', error=str(e))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear() 
    return redirect(url_for('index'))



@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        crowd = request.form['crowd']
        chips = request.form['chips']
        queue = request.form['queue']
        resource_id = str(uuid4())

   
        supabase.table('resources').insert({'id': resource_id, 'name': title}).execute()


        status_data = {
            'id': str(uuid4()),
            'resource_id': resource_id,
            'status_message': description,
            'crowd_level': crowd,
            'chips_available': chips,
            'queue_length': queue,
            'user_id': session['user_id']
        }
        supabase.table('status_updates').insert(status_data).execute()
        return redirect(url_for('index'))
    return render_template('create_post.html')

@app.route('/update_post/<post_id>', methods=['POST'])
@login_required
def update_post(post_id):

    description = request.form['description']
    crowd = request.form['crowd']
    chips = request.form['chips']
    queue = request.form['queue']

    # FIX 5: This logic now inserts a new status update, which is a more robust pattern
  
    supabase.table('status_updates').insert({
        'id': str(uuid4()),
        'resource_id': post_id,
        'status_message': description,
        'crowd_level': crowd,
        'chips_available': chips,
        'queue_length': queue,
        'user_id': session['user_id'] 
    }).execute()

    return redirect(url_for('index'))

@app.route('/upvote', methods=['POST'])
@login_required
def upvote():
    resource_id = request.json.get('resource_id')
    user_id = session.get('user_id')

    if not resource_id or not user_id:
        return jsonify({'error': 'Missing data'}), 400


    existing_upvote = supabase.table('upvotes').select('id').eq('resource_id', resource_id).eq('user_id', user_id).execute()
    if existing_upvote.data:
        return jsonify({'error': 'Already upvoted'}), 409


    supabase.table('upvotes').insert({
        'id': str(uuid4()),
        'resource_id': resource_id,
        'user_id': user_id
    }).execute()

 
    count_response = supabase.table('upvotes').select('id', count='exact').eq('resource_id', resource_id).execute()
    new_count = count_response.count if hasattr(count_response, 'count') else 0
    return jsonify({'success': True, 'upvotes': new_count})


if __name__ == '__main__':
    app.run(debug=True)