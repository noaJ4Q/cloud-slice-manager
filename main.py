from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

USERS = [
  {
    'id': 1,
    'username': 'branko',
    'password': 'branko',
    'role': 'manager'
  },
  {
    'id': 2,
    'username': 'willy',
    'password': 'willy',
    'role': 'admin'
  },
  {
    'id': 3,
    'username': 'mavend',
    'password': 'mavend',
    'role': 'client'
  },
]

SLICES = [
  {
    'id': 1,
    'name': 'Slice 1',
    'user': 3,
    'topology': 'Malla',
    'vms': 2,
    'zone': 'Zona 1',
    'created': '2021-06-01 10:00:00',
    'status': 'active'
  },
  {
    'id': 2,
    'name': 'Slice 2',
    'user': 3,
    'topology': 'Anillo',
    'vms': 3,
    'zone': 'Zona 2',
    'created': '2021-06-01 10:00:00',
    'status': 'active'
  }
]

@app.route('/auth', methods=['POST'])
def auth_user():

  # Get the username and password from JSON request
  username = request.json['username']
  password = request.json['password']

  user = validate_user(username, password)
  if user: 
    token = jwt.encode({'role': user['role']}, 'secret', algorithm='HS256')
    return jsonify({'message': 'success', 'token': token})
  else:
    return jsonify({'message': 'Invalid username or password'})

@app.route('/slices', methods=['GET'])
def list_slices():
  token = request.headers.get('Authorization')
  try:
    decoded = jwt.decode(token, 'secret', algorithms=['HS256'])
    if decoded['role'] == 'manager':
      return jsonify({'message': 'success', 'slices': SLICES})
    else:
      return jsonify({'message': 'Unauthorized access'}), 401
  except jwt.ExpiredSignatureError:
    return jsonify({'message': 'Token expired'}), 401
  except jwt.InvalidTokenError:
    return jsonify({'message': 'Invalid token'}), 401

def validate_user(username, password):
  for user in USERS:
    if user['username'] == username and user['password'] == password:
      return user
  return None

if __name__=='__main__':
  app.run()