import datetime
import math
from settings import templates, BASE_HOST
from starlette.responses import RedirectResponse
from starlette.authentication import requires
from tortoise.query_utils import Q
from questions.forms import (
    QuestionForm, AnswerForm, AnswerLikesForm, QuestionLikesForm
)
from models import Question, User, Answer, Tag


async def questions_all(request):
    """
    All questions
    """
    path = request.url.path
    page_query = request.query_params['page']
    result = await Question.all()
    count = len(result)
    page = int(page_query)
    per = 2
    totalPages = int(math.ceil(count / per))
    offset = per * (page - 1)
    results = await Question.all().prefetch_related(
        "user", "tags").limit(per).offset(offset).order_by('-id')
    return templates.TemplateResponse(
        "questions/questions.html",
        {
            "request": request,
            "results": results,
            "path": path,
            "totalPages": totalPages,
            "page_query": page_query
        },
    )


async def question(request):
    """
    Single question
    """
    id = request.path_params["id"]
    path = request.url.path
    results = await Question.get(id=id).prefetch_related("user", "tags")
    # update question views per session
    session_key = 'viewed_question_{}'.format(results.id)
    if not request.session.get(session_key, False):
        results.view += 1
        await results.save()
        request.session[session_key] = True
    # question and answer likes per session
    try:
        qus_data = await request.form()
        question_likes_form = QuestionLikesForm(qus_data)
        ans_data = await request.form()
        likes_form = AnswerLikesForm(ans_data)
        if request.method == "POST":
            result = await Question.get(
                id=question_likes_form.question_id.data)
            session_key_quslike = 'liked_question_{}'.format(result.id)
            if not request.session.get(session_key_quslike, False):
                result.question_like += 1
                await result.save()
                request.session[session_key_quslike] = True
                return RedirectResponse(BASE_HOST + path, status_code=302)
    except ValueError:
        if request.method == "POST":
            result = await Answer.get(id=likes_form.answer_id.data)
            session_key_like = 'liked_answer_{}'.format(result.id)
            if not request.session.get(session_key_like, False):
                result.answer_like += 1
                await result.save()
                request.session[session_key_like] = True
                return RedirectResponse(BASE_HOST + path, status_code=302)
    answer_results = (
        await Answer.all()
        .prefetch_related("ans_user", "question")
        .filter(question__id=id)
        .order_by("-id")
    )
    return templates.TemplateResponse(
        "questions/question.html",
        {
            "request": request,
            "item": results,
            "path": path,
            "likes_form": likes_form,
            "question_likes_form": question_likes_form,
            "answer_results": answer_results,
            "answer_count": len(answer_results),
        },
    )


@requires("authenticated")
async def answer_create(request):
    """
    Answer form
    """
    id = int(request.query_params['next'].split('/')[2])
    next = request.query_params['next']
    results = await Question.get(id=id).prefetch_related("user", "tags")
    session_user = request.user.username
    data = await request.form()
    form = AnswerForm(data)
    result = await User.get(username=session_user)
    if request.method == "POST" and form.validate():
        query = Answer(
            content=form.content.data,
            created=datetime.datetime.now(),
            answer_like=0,
            question_id=results.id,
            ans_user_id=result.id,
        )
        await query.save()
        results.answer_count += 1
        await results.save()
        return RedirectResponse(BASE_HOST + next, status_code=302)
    return templates.TemplateResponse(
        "questions/answer_create.html", {
            "request": request,
            "form": form,
            "next": next
        }
    )


@requires("authenticated", redirect="index")
async def question_create(request):
    """
    Question form
    """
    session_user = request.user.username
    results = await User.get(username=session_user)
    data = await request.form()
    form = QuestionForm(data)
    title = form.title.data
    if request.method == "POST" and form.validate():
        if "," in form.tags.data:
            query = Question(
                title=title,
                slug="-".join(title.lower().split()),
                content=form.content.data,
                created=datetime.datetime.now(),
                view=0,
                question_like=0,
                answer_count=0,
                user_id=results.id,
            )
            await query.save()
            tags = []
            # split tags and insert in db
            for idx, item in enumerate(form.tags.data.split(",")):
                tag = Tag(name=item.lower())
                await tag.save()
                tags.append(tag)
                await query.tags.add(tags[idx])
            return RedirectResponse(url="/questions/?page=1", status_code=302)
        tag_error = "Tags must be comma-separated"
        return templates.TemplateResponse(
            "questions/question_create.html",
            {"request": request, "form": form, "tag_error": tag_error},
        )
    return templates.TemplateResponse(
        "questions/question_create.html", {"request": request, "form": form}
    )


async def tags(request):
    """
    All tags
    """
    tag = request.path_params["tag"]
    results = (
        await Question.all()
        .prefetch_related("user", "tags")
        .filter(tags__name=tag)
        .order_by("-id")
    )
    return templates.TemplateResponse(
        "questions/tags.html", {"request": request,
                                "results": results, "tag": tag}
    )


async def search(request):
    """
    Search questions
    """
    q = request.query_params['q']
    results = (
        await Question.all()
        .prefetch_related("user", "tags")
        .filter(Q(title__icontains=q) |
                Q(content__icontains=q) |
                Q(user__username__icontains=q) |
                Q(tags__name__icontains=q)).distinct()
        .order_by("-id")
    )
    return templates.TemplateResponse(
        "questions/search.html", {"request": request,
                                  "results": results,
                                  "q": q}
    )
