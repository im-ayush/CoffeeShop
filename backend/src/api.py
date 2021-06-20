import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth
import sys

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_drinks():
    try:
        drinks = Drink.query.all()
        drinks = [drink.short() for drink in drinks]
    except:
        abort(500)
    return jsonify({
                'success':True,
                'drinks':drinks,
                }), 200

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()
        drinks = [drink.long() for drink in drinks]
    except:
        abort(500)
    return jsonify({
                'success':True,
                'drinks':drinks,
                }), 200

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_new_drink(payload):
    body = request.get_json()

    title = body.get('title', None)
    if title is None:
        abort(400)

    recipe = body.get('recipe', [])
    if len(recipe)==0:
        abort(400)

    try:
        new_drink = Drink(
                        title=title,
                        recipe=json.dumps(recipe)
                        )
        db.session.add(new_drink)
        db.session.commit()

        return jsonify({
                    'success':True,
                    'drinks':[new_drink.long()],
                    }), 200

    except Exception as e:
        db.session.rollback()
        print(sys.exc_info())
        abort(422)

    finally:
        db.session.close()

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    body = request.get_json()

    try:
        drink = Drink.query.filter_by(id=id).one_or_none()
        if drink is None:
            abort(404)

        if 'title' in body:
            drink.title = body['title']
        if 'recipe' in body:
            drink.recipe = json.dumps(body['recipe'])

        drink.update()
        db.session.commit()

        return jsonify({
                    'success':True,
                    'drinks':[drink.long()],
                    }), 200

    except Exception as e:
        db.session.rollback()
        print(sys.exc_info())
        abort(422)

    finally:
        db.session.close()

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter_by(id=id).one_or_none()
        if drink is None:
            abort(404)
        drink.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(sys.exc_info())
        abort(422)
    finally:
        db.session.close()

    return jsonify({
                'success':True,
                'delete':id
                })

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success':False,
        'error': 404,
        'message': 'resource not found',
        }), 404

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success':False,
        'error': 500,
        'message': 'internal server error',
        }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success':False,
        'error': 400,
        'message': 'bad request',
        }), 400

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(e):
    response = jsonify(e.error)
    response.status_code = e.status_code
    return response
