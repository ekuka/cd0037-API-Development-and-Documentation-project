import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins.
    Delete the sample route after completing the TODOs
    """

    # CORS(app)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization, true'
            )
        response.headers.add(
            'Access-Control-Allow-Headers',
            'GET, POST, PATCH, DELETE, OPTIONS'
            )
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route("/categories")
    def request_categories():
        all_categories = {}
        categories = Category.query.order_by(Category.id).all()
        for category in categories:
            all_categories[category.id] = category.type
        return jsonify({
            "success": True,
            "categories": all_categories,
            "total_categories": len(categories)
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of
    the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_questions():
        categories = Category.query.order_by(Category.id).all()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        current_category = {}
        for category in categories:
            current_category[category.id] = category.type

        if len(current_questions) == 0:
            abort(404)
        return jsonify({
            "success": True,
            "current_category": "Art",
            "categories": current_category,
            "questions": current_questions,
            "total_questions": len(Question.query.all())
        })
    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
     the question will be removed.
    This removal will persist in the database and
    when you refresh the page.
    """
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "deleted": question_id,
                "questions": current_questions,
                "total_questions": len(Question.query.all())
            })
        except:
            abort(422)
    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will
    appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_category = body.get("category", None)
        new_difficulty = body.get("difficulty", None)

        try:
            question = Question(
                question=new_question,
                answer=new_answer, category=new_category,
                difficulty=new_difficulty
            )
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "created": question.id,
                "questions": current_questions,
                "total_questions": len(Question.query.all())
            })
        except:
            abort(422)
    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route("/searchs", methods=["POST"])
    def search_questions():
        body = request.get_json()
        searchTerm = body.get("searchTerm", None)
        categories = Category.query.order_by(Category.id).all()
        current_category = {}
        try:
            selection = Question.query.order_by(Question.id).filter(
                Question.question.ilike("%{}%".format(searchTerm))
            )
            current_questions = paginate_questions(request, selection)
            current_category = [category.type for category in categories]

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(selection.all()),
                    "current_category": current_category
                }
            )
        except:
            abort(405)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:category_id>/questions")
    def get_questions_based_on_category(category_id):
        selection = Question.query.filter(
            Question.category == str(category_id)).all()

        selected_categories = Category.query.filter(
            Category.id == category_id).all()

        questions = paginate_questions(request, selection)
        current_category = [category.type for category in selected_categories]
        try:
            return jsonify({
                "success": True,
                # "questions": [question.question for
                # question in questions],
                "questions": questions,
                "current_category": current_category[0],
                "total_questions": len(questions)
            })
        except:
            abort(404)
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route("/quizzes", methods=['POST'])
    def quiz():
        try:
            request_data = json.loads(request.data)
            if (('quiz_category' in request_data and 'id' in request_data['quiz_category']) and
                'previous_questions' in request_data):
                questions = Question.query.filter_by(
                    category=request_data['quiz_category']['id']
                ).filter(
                    Question.id.notin_(request_data["previous_questions"])
                ).all()
                len_of_available_question = len(questions)
                if len_of_available_question > 0:
                    return jsonify({
                        "success": True,
                        "question": Question.format(questions[random.randrange(0, len_of_available_question)])
                    })
                else:
                    return jsonify({
                        "success": True,
                        "question": None
                    })
            abort(404)
        except:
            abort(422)
        
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 404,
                "message": "resource not found"
                }),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                "success": False,
                "error": 422,
                "message": "unprocessable"
            }),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
            }), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 405,
                "message": "method not allowed"
             }), 405
        )

    return app
