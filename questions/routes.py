from starlette.routing import Route, Router
from questions.views import (
    questions_all,
    question,
    question_create,
    question_edit,
    question_delete,
    answer_create,
    answer_delete,
    answer_edit,
    tags,
    search,
    tags_categories,
    accepted_answer
)

questions_routes = Router([
    Route("/", endpoint=questions_all,
          methods=["GET", "POST"], name="questions_all"),
    Route("/{id:int}/{slug:str}", endpoint=question,
          methods=["GET", "POST"], name="question"),
    Route("/create", endpoint=question_create,
          methods=["GET", "POST"], name="question_create"),
    Route("/edit/{id:int}", endpoint=question_edit,
          methods=["GET", "POST"], name="question_edit"),
    Route("/delete/{id:int}", endpoint=question_delete,
          methods=["GET", "POST"], name="question_delete"),
    Route("/answer-create", endpoint=answer_create,
          methods=["GET", "POST"], name="answer_create"),
    Route("/answer-edit/{id:int}", endpoint=answer_edit,
          methods=["GET", "POST"], name="answer_edit"),
    Route("/answer-delete/{id:int}", endpoint=answer_delete,
          methods=["GET", "POST"], name="answer_delete"),
    Route("/tags/{tag:str}", endpoint=tags, methods=["GET"], name="tags"),
    Route("/search", endpoint=search, methods=["GET"], name="search"),
    Route("/categories", endpoint=tags_categories,
          methods=["GET"], name="tags_categories"),
    Route("/accepted-answer", endpoint=accepted_answer,
          methods=["GET", "POST"], name="accepted_answer")
])