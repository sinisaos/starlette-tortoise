import datetime
import math
from settings import templates, BASE_HOST
from starlette.responses import RedirectResponse
from starlette.authentication import requires
from questions.forms import QuestionForm, AnswerForm
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
    results.views += 1
    await results.save()
    data = await request.form()
    form = AnswerForm(data)
    if request.user.is_authenticated:
        result = await User.get(username=request.user.username)
        if request.method == "POST" and form.validate():
            query = Answer(
                content=form.content.data,
                created=datetime.datetime.now(),
                question_id=results.id,
                ans_user_id=result.id,
            )
            await query.save()
            results.answer_count += 1
            await results.save()
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
            "form": form,
            "answer_results": answer_results,
            "answer_count": len(answer_results),
        },
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
                views=0,
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
