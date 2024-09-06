from flask import Flask, request, jsonify, send_from_directory, make_response, redirect, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity,  unset_jwt_cookies, verify_jwt_in_request, set_access_cookies
import bcrypt
import os
from models import db, User, FileMetadata
from config import Config
from werkzeug.utils import secure_filename
import secrets
from flask import render_template
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os
import uuid  # For generating unique identifiers
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)
csrf = CSRFProtect(app)

if app.config['TESTING']:
    csrf._disable = True
else:
    csrf.init_app(app)



@app.route('/')
def index():
    current_user = False
    file_list = False
    try:
        verify_jwt_in_request()  # This will check for the JWT token in cookies
        current_user = get_jwt_identity()['username']  # Get the current user's identity from the token
        current_user = current_user if current_user else False
        if current_user:
            user = User.query.filter_by(username=current_user).first()

            # Retrieve the user's files from the database
            files = FileMetadata.query.filter_by(user_id=user.id).all()
            print("files : ", files)
            # Format the response
            file_list = [{
                "filename": file.filename,
                "size": file.size ,
                "file_format" : file.file_format,
                "upload_time": file.upload_time
            } for file in files]

            
    except Exception as e:
        return render_template('index.html',  username=current_user, books=file_list)
    
    return render_template('index.html',  username=current_user, books=file_list)



@app.route('/login', methods=['POST', 'GET'])
def login():
    try:
        verify_jwt_in_request()  # This will check for the JWT token in cookies
        current_user = get_jwt_identity()['username']  # Get the current user's identity from the token
        print("current_user:", current_user )
        if current_user:
            return redirect('/profile')
    except:
        pass

    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
            access_token = create_access_token(identity={'username': user.username, 'id': user.id})
            response = jsonify({ "message": "Token set successfully!"})
            set_access_cookies(response, access_token)
            return response, 200
        else:
            return jsonify({"message": "Invalid credentials!"}), 401
    else:
        return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    try:
        verify_jwt_in_request()  # This will check for the JWT token in cookies
        current_user = get_jwt_identity()['username']  # Get the current user's identity from the token
        print("current_user:", current_user )
        if current_user:
            return redirect('/profile')
    except:
        pass

    if request.method == "POST":
        data = request.get_json()
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        try:
            new_user = User(username=data['username'], password_hash=hashed_password.decode('utf-8'))
            db.session.add(new_user)
            db.session.commit()
            access_token = create_access_token(identity={'username': new_user.username, 'id': new_user.id})
            response = jsonify({ "message": "Token set successfully!"})
            set_access_cookies(response, access_token)
            return response, 201
        
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Username already exist!" }), 400

        except Exception as e:
            return jsonify({"message": "User Registration Failed!" }), 500
    else:
        return render_template('register.html')


@app.route('/logout', methods=['GET'])
@jwt_required()
def logout():
    response = make_response(redirect('/'))  # Redirect to the homepage ("/")
    unset_jwt_cookies(response)  # Remove the JWT cookies to log the user out
    return response


@app.route('/profile')
@jwt_required()  # Ensure the user is logged in
def profile():
    current_user = get_jwt_identity()['username']  # Assuming JWT identity is the username
    return render_template('profile.html', username=current_user)


@app.route('/reset-password', methods=['POST', 'GET'])
def reset_password():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({"message": "User not found!"}), 404

        reset_token = secrets.token_urlsafe()
        user.reset_token = reset_token
        db.session.commit()

        reset_link = url_for('reset_password_confirm', token=reset_token, _external=True)
        return jsonify({"message": "Password reset link sent!", "reset_link": reset_link})
    else:
        return render_template('reset_password.html')
    

@app.route('/reset-password/<token>', methods=['POST', 'GET'])
def reset_password_confirm(token):
    if request.method == 'POST':
        data = request.get_json()
        if not data['new_password'] == data['confirm_password']:
            return jsonify({"message": "Password didn't match!"})
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return jsonify({"message": "Invalid token!"}), 400

        new_password_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
        user.password_hash = new_password_hash.decode('utf-8')
        user.reset_token = None
        db.session.commit()
        return jsonify({"message": "Password reset successful!"})
    else:
       return render_template('confirm_reset_password.html', token=token)


@app.route('/upload', methods=['POST', 'GET'])
@jwt_required()
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"message": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "No selected file"}), 400

        if file:
            filename = secure_filename(file.filename)
            file_extension = os.path.splitext(filename)[1]
            base_filename = os.path.splitext(filename)[0]
            new_filename = filename
            upload_folder = app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, new_filename)
            while os.path.exists(file_path):
                unique_id = str(uuid.uuid4().hex)
                new_filename = f"{base_filename}_{unique_id}{file_extension}"
                file_path = os.path.join(upload_folder, new_filename)
                

            file.save(file_path)

            size_bytes = os.path.getsize(file_path) 
           
            if size_bytes < 1024:
                size = f"{size_bytes} Bytes"
            elif size_bytes < 1024**2:
                size = f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024**3:
                size = f"{size_bytes / 1024**2:.2f} MB"
            elif size_bytes < 1024**4:
                size = f"{size_bytes / 1024**3:.2f} GB"
            else:
                size = f"{size_bytes / 1024**4:.2f} TB"
        
            # Get user ID from JWT token
            user_id = get_jwt_identity()['id']  
            # Save file metadata in the database
            file_metadata = FileMetadata(filename=new_filename, user_id=user_id,file_format = file_extension.rsplit('.', 1)[-1].upper(), size=size)
            db.session.add(file_metadata)
            db.session.commit()
            
            return jsonify({"message": "File uploaded successfully!", "Filename": new_filename}), 201
    else:
        username = get_jwt_identity()['username']
    
        return render_template('upload_file.html', username=username)


@app.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
    print(f"Requested file: {filename}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)



@app.route('/delete/<filename>', methods=['POST'])
@jwt_required()
def delete_file(filename):
    if request.method == 'POST':
        if request.form.get('_method') == 'DELETE':
            user_id = get_jwt_identity()['id']
            file_metadata = FileMetadata.query.filter_by(filename=filename, user_id=user_id).first()

            if not file_metadata:
                return jsonify({"message": "File not found or you do not have permission to delete this file."}), 404

            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

                db.session.delete(file_metadata)
                db.session.commit()

                return jsonify({"message": "File deleted successfully!"}), 200
            except Exception as e:
                print(e)
                return jsonify({"message": "An error occurred while deleting the file."}), 500
        else:
            return jsonify({"message": "Invalid request method."}), 405