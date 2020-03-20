import datetime
import itertools as it
from settings import templates, BASE_HOST
from starlette.responses import RedirectResponse
from starlette.authentication import requires
from tortoise.query_utils import Q
from tortoise.transactions import in_transaction
from utils import pagination
from questions.forms import (
    QuestionForm,
    AnswerForm,
    QuestionEditForm,
    AnswerLikesForm,
    AnswerEditForm,
    QuestionLikesForm,
    AcceptedAnswerForm
)
from accounts.models import (
    User,
    ADMIN
)
from questions.models import (
    Question,
    Answer,
    Tag,
)


async def questions_all(request):
    """
    All questions
    """
    page_query = pagination.get_page_number(url=request.url)
    count = await Question.all().count()
    paginator = pagination.Pagination(page_query, count)
    results = (
        await Question.all()
        .prefetch_related("user", "tags")
        .limit(paginator.page_size)
        .offset(paginator.offset())
        .order_by('-id')
    )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    page_controls = pagination.get_page_controls(
        url=request.url,
        current_page=paginator.current_page(),
        total_pages=paginator.total_pages()
    )
    return templates.TemplateResponse(
        "questions/questions.html",
        {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls,
        }
    )


async def questions_solved(request):
    """
    Solved questions
    """
    page_query = pagination.get_page_number(url=request.url)
    count = await Question.filter(accepted_answer=True).count()
    paginator = pagination.Pagination(page_query, count)
    results = (
        await Question.filter(accepted_answer=True)
        .prefetch_related("user", "tags")
        .limit(paginator.page_size)
        .offset(paginator.offset())
        .order_by('-id')
    )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    page_controls = pagination.get_page_controls(
        url=request.url,
        current_page=paginator.current_page(),
        total_pages=paginator.total_pages()
    )
    return templates.TemplateResponse(
        "questions/questions.html",
        {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls
        }
    )


async def questions_open(request):
    """
    Unsolved questions
    """
    page_query = pagination.get_page_number(url=request.url)
    count = await Question.filter(accepted_answer=False).count()
    paginator = pagination.Pagination(page_query, count)
    results = (
        await Question.filter(accepted_answer=False)
        .prefetch_related("user", "tags")
        .limit(paginator.page_size)
        .offset(paginator.offset())
        .order_by('-id')
    )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    page_controls = pagination.get_page_controls(
        url=request.url,
        current_page=paginator.current_page(),
        total_pages=paginator.total_pages()
    )
    return templates.TemplateResponse(
        "questions/questions.html",
        {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls
        }
    )


async def questions_viewed(request):
    """
    Most viewed questions
    """
    page_query = pagination.get_page_number(url=request.url)
    count = await Question.all().count()
    paginator = pagination.Pagination(page_query, count)
    results = (
        await Question.all()
        .prefetch_related("user", "tags")
        .limit(paginator.page_size)
        .offset(paginator.offset())
        .order_by('-view')
    )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    page_controls = pagination.get_page_controls(
        url=request.url,
        current_page=paginator.current_page(),
        total_pages=paginator.total_pages()
    )
    return templates.TemplateResponse(
        "questions/questions.html",
        {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls
        }
    )


async def questions_oldest(request):
    """
    Oldest questions
    """
    page_query = pagination.get_page_number(url=request.url)
    count = await Question.all().count()
    paginator = pagination.Pagination(page_query, count)
    results = (
        await Question.all()
        .prefetch_related("user", "tags")
        .limit(paginator.page_size)
        .offset(paginator.offset())
        .order_by('id')
    )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    page_controls = pagination.get_page_controls(
        url=request.url,
        current_page=paginator.current_page(),
        total_pages=paginator.total_pages()
    )
    return templates.TemplateResponse(
        "questions/questions.html",
        {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls
        }
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
        # possible to insert only one tag without error
        if "," in form.tags.data or len((form.tags.data).split()) == 1:
            query = Question(
                title=title,
                slug="-".join(title.lower().split()),
                content=form.content.data,
                created=datetime.datetime.now(),
                view=0,
                question_like=0,
                user_id=results.id,
            )
            await query.save()
            tags = []
            # split tags and make sure that is valid tags list without empty
            # space and than insert in db
            valid_tags_list = [i for i in form.tags.data.split(",") if i != '']
            for idx, item in enumerate(valid_tags_list):
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


@requires("authenticated")
async def question_edit(request):
    """
    Question edit form
    """
    id = request.path_params["id"]
    session_user = request.user.username
    results = await User.get(username=session_user)
    question = await Question.get(id=id)
    data = await request.form()
    form = QuestionEditForm(data)
    new_form_value, form.content.data = form.content.data, question.content
    title = form.title.data
    if request.method == "POST" and form.validate():
        query = Question(
            id=question.id,
            title=title,
            slug="-".join(title.lower().split()),
            content=new_form_value,
            created=datetime.datetime.now(),
            view=question.view,
            question_like=question.question_like,
            user_id=results.id,
        )
        await query.save()
        if request.user.username == ADMIN:
            return RedirectResponse(url="/accounts/dashboard", status_code=302)
        return RedirectResponse(url="/accounts/profile", status_code=302)
    return templates.TemplateResponse(
        "questions/question_edit.html", {
            "request": request,
            "form": form,
            "question": question
        }
    )


@requires("authenticated")
async def question_delete(request):
    """
    Delete question
    """
    id = request.path_params["id"]
    if request.method == "POST":
        # delete all related tags
        async with in_transaction() as conn:
            await conn.execute_query(
                f"DELETE FROM tag WHERE tag.id IN \
                (SELECT question_tag.tag_id FROM question \
                JOIN question_tag ON question_tag.question_id = question.id \
                WHERE question.id={id})"
            )
        await Question.get(id=id).delete()
        if request.user.username == ADMIN:
            return RedirectResponse(url="/accounts/dashboard", status_code=302)
        return RedirectResponse(url="/accounts/profile", status_code=302)


@requires("authenticated")
async def answer_create(request):
    """
    Answer form
    """
    id = int(request.query_params['next'].split('/')[2])
    next = request.query_params['next']
    results = (
        await Question.get(id=id)
        .prefetch_related("user", "tags")
    )
    session_user = request.user.username
    data = await request.form()
    form = AnswerForm(data)
    result = await User.get(username=session_user)
    if request.method == "POST" and form.validate():
        query = Answer(
            content=form.content.data,
            created=datetime.datetime.now(),
            answer_like=0,
            is_accepted_answer=0,
            question_id=results.id,
            ans_user_id=result.id,
        )
        await query.save()
        return RedirectResponse(BASE_HOST + next, status_code=302)
    return templates.TemplateResponse(
        "questions/answer_create.html", {
            "request": request,
            "form": form,
            "next": next
        }
    )


@requires("authenticated")
async def answer_edit(request):
    """
    Answer edit form
    """
    id = request.path_params["id"]
    answer = await Answer.get(id=id)
    data = await request.form()
    form = AnswerEditForm(data)
    new_form_value, form.content.data = form.content.data, answer.content
    if request.method == "POST" and form.validate():
        query = Answer(
            id=answer.id,
            content=new_form_value,
            created=datetime.datetime.now(),
            answer_like=answer.answer_like,
            is_accepted_answer=answer.is_accepted_answer,
            question_id=answer.question_id,
            ans_user_id=answer.ans_user_id,
        )
        await query.save()
        if request.user.username == ADMIN:
            return RedirectResponse(url="/accounts/dashboard", status_code=302)
        return RedirectResponse(url="/accounts/profile", status_code=302)
    return templates.TemplateResponse(
        "questions/answer_edit.html", {
            "request": request,
            "form": form,
            "answer": answer
        }
    )


@requires("authenticated")
async def answer_delete(request):
    """
    Delete answer
    """
    id = request.path_params["id"]
    answer = await Answer.get(id=id)
    question = await Question.get(id=answer.question_id)
    if request.method == "POST":
        if answer.is_accepted_answer:
            question.accepted_answer = False
            await question.save()
        await Answer.get(id=id).delete()
        if request.user.username == ADMIN:
            return RedirectResponse(url="/accounts/dashboard", status_code=302)
        return RedirectResponse(url="/accounts/profile", status_code=302)


@requires("authenticated")
async def accepted_answer(request):
    """
    Accepted answer form
    """
    id = int(request.query_params['next'].split('/')[2])
    answer_id = int(request.query_params['next'].split('/')[-1])
    path = '/'.join((request.query_params['next']).split('/')[:-1])
    print(path)
    res = await Question.get(id=id)
    data = await request.form()
    form = AcceptedAnswerForm(data)
    result = await Answer.get(pk=answer_id)
    if request.method == "POST":
        result.is_accepted_answer = True
        await result.save()
        res.accepted_answer = True
        await res.save()
        return RedirectResponse(BASE_HOST + path, status_code=302)
    return templates.TemplateResponse(
        "questions/accepted_answer.html", {
            "request": request,
            "form": form,
            "result": result,
            "res": res,
            "path": path
        }
    )


async def tags(request):
    """
    All tags
    """
    page_query = pagination.get_page_number(url=request.url)
    tag = request.path_params["tag"]
    count = (
        await Question.all()
        .prefetch_related("user", "tags")
        .filter(tags__name=tag)
        .count()
    )
    paginator = pagination.Pagination(page_query, count)
    results = (
        await Question.all()
        .prefetch_related("user", "tags")
        .filter(tags__name=tag)
        .limit(paginator.page_size)
        .offset(paginator.offset())
        .order_by("-id")
    )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    page_controls = pagination.get_page_controls(
        url=request.url,
        current_page=paginator.current_page(),
        total_pages=paginator.total_pages()
    )
    return templates.TemplateResponse(
        "questions/tags.html", {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls,
            "tag": tag
        }
    )


async def search(request):
    """
    Search questions
    """
    try:
        page_query = pagination.get_page_number(url=request.url)
        q = request.query_params['q']
        count = (
            await Question.all()
            .prefetch_related("user")
            .filter(Q(title__icontains=q) |
                    Q(content__icontains=q) |
                    Q(user__username__icontains=q))
            .distinct()
            .count()
        )
        paginator = pagination.Pagination(page_query, count)
        results = (
            await Question.all()
            .prefetch_related("user", "tags")
            .filter(Q(title__icontains=q) |
                    Q(content__icontains=q) |
                    Q(user__username__icontains=q) |
                    Q(tags__name__icontains=q))
            .distinct()
            .limit(paginator.page_size)
            .offset(paginator.offset())
        )
        page_controls = pagination.get_page_controls(
            url=request.url,
            current_page=paginator.current_page(),
            total_pages=paginator.total_pages()
        )
    except KeyError:
        page_query = pagination.get_page_number(url=request.url)
        count = await Question.all().count()
        paginator = pagination.Pagination(page_query, count)
        results = (
            await Question.all()
            .prefetch_related("user", "tags")
            .limit(paginator.page_size)
            .offset(paginator.offset())
        )
        page_controls = pagination.get_page_controls(
            url=request.url,
            current_page=paginator.current_page(),
            total_pages=paginator.total_pages()
        )
    answer_count = []
    for row in results:
        r = (
            await Answer.all()
            .prefetch_related("question")
            .filter(question__id=row.id).count()
        )
        answer_count.append(r)
    return templates.TemplateResponse(
        "questions/search.html", {
            "request": request,
            "results": zip(results, answer_count),
            "page_controls": page_controls,
            "count": count,
            "q": q
        }
    )


async def tags_categories(request):
    """
    Tags categories
    """
    # use itertools.groupby to simulate SQL GROUP BY
    results = await Tag.all().order_by("name").values("name")
    categories_tags = [
        (k, sum(1 for i in g)) for k, g in it.groupby(results)
    ]
    return templates.TemplateResponse(
        "questions/tags_categories.html", {
            "request": request,
            "categories_tags": categories_tags
        }
    )
