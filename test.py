import pytest
import json
from app import app, db
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture(scope='module')
def test_client():
    # Set up the test client and database
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['JWT_SECRET_KEY'] = '4fb6763d012413e746b7a65d4fb06c891eff2d29c804a939abee26e104859f27'
    app.config['UPLOAD_FOLDER'] = 'uploads'

    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
        yield testing_client
        with app.app_context():
            db.drop_all()

def test_register(test_client):
    # Simulate a session in the test client
    response = test_client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })

    # Check the response
    assert response.status_code == 201
    assert b"Token set successfully!" in response.data


    
def test_login(test_client):
    # Register a user first
    test_client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })

    # Attempt to log in
    response = test_client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)  # Follow the redirect to the final destination


    # Check that the login was successful and redirected correctly
    if response.status_code == 200:
        assert b"Welcome" in response.data
    else:
        # If the status code is neither 200 nor 302, fail the test
        assert False, f"Unexpected status code: {response.status_code}"

def test_upload_file(test_client):
    # Login first to get a JWT token
    test_client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Create a test file
    with open('test_file.txt', 'w') as f:
        f.write('This is a test file.')

    with open('test_file.txt', 'rb') as file:
        data = {
            'file': (file, 'test_file.txt')
        }
        response = test_client.post('/upload', content_type='multipart/form-data', data=data)
    
    os.remove('test_file.txt')  # Clean up the test file
    
    assert response.status_code == 201
    assert b"File uploaded successfully!" in response.data

def test_download_file(test_client):
    # Upload a file first
    test_upload_file(test_client)
    
    response = test_client.get('/download/test_file.txt')
    assert response.status_code == 200




def test_reset_password(test_client):
    # Register a user first
    test_client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    response = test_client.post('/reset-password', json={
        'username': 'testuser'
    })
    assert response.status_code == 200
    assert b"Password reset link sent!" in response.data

def test_reset_password_confirm(test_client):
    # Register and reset password for the user first
    test_client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    response = test_client.post('/reset-password', json={
        'username': 'testuser'
    })

    reset_link = json.loads(response.data)['reset_link']

    # Extract token from reset link
    token = reset_link.split('/')[-1]
    
    response = test_client.post(f'/reset-password/{token}', json={
        'new_password': 'newpassword',
        'confirm_password': 'newpassword'
    })

    assert response.status_code == 200
    assert b"Password reset successful!" in response.data

def test_logout(test_client):
    # Login first to get a JWT token
    test_client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    response = test_client.get('/logout')
    assert response.status_code == 302
    assert response.headers['Location'] == '/'

if __name__ == "__main__":
    pytest.main()
