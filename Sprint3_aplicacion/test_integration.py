import pytest
from server import app as _app, db
from database import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    _app.config['TESTING'] = True
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with _app.app_context():
        db.create_all()
    yield _app
    with _app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_user_registration(client):
    with client.application.app_context():
        response = client.post('/register', json={
            'nombre': 'Test',
            'apellidos': 'User',
            'correo': 'test@example.com',
            'telefono': '1234567890',
            'password': 'testpassword'
        })
        assert response.status_code == 302
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None

def test_user_login(client):
    with client.application.app_context():
        hashed_password = generate_password_hash('testpassword')
        user = User(username='Test', email='test@example.com', password=hashed_password)
        db.session.add(user)
        db.session.commit()

        # Intenta hacer login con el usuario creado
        response = client.post('/login', json={
            'correo': 'test@example.com',
            'password': 'testpassword'
        })
        assert response.status_code == 302


def test_data_update(client):
    response = client.get('/update-data')
    assert response.status_code == 200
    # Realiza aquí las comprobaciones adicionales según sea necesario

