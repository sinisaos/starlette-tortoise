import datetime
from settings import templates, BASE_HOST
from starlette.responses import RedirectResponse
from starlette.authentication import requires
from tortoise.transactions import in_transaction
from accounts.forms import RegistrationForm, LoginForm
from accounts.models import (
    User,
    check_password,
    generate_jwt,
    hash_password,
    ADMIN,
)
from questions.models import (
    Question,
    Answer
)


async def register(request):
    """
    Validate form, register and authenticate user with JWT token
    """
    results = await User.all()
    data = await request.form()
    form = RegistrationForm(data)
    username = form.username.data
    email = form.email.data
    password = form.password.data
    if request.method == "POST" and form.validate():
        for result in results:
            if email == result.email or username == result.username:
                user_error = "User with that email or username already exists."
                return templates.TemplateResponse(
                    "accounts/register.html",
                    {
                        "request": request,
                        "form": form,
                        "user_error": user_error
                    },
                )
        query = User(
            username=username,
            email=email,
            joined=datetime.datetime.now(),
            last_login=datetime.datetime.now(),
            login_count=1,
            password=hash_password(password),
        )
        await query.save()
        user_query = await User.get(
            username=username)
        hashed_password = user_query.password
        valid_password = check_password(password, hashed_password)
        response = RedirectResponse(url="/", status_code=302)
        if valid_password:
            response.set_cookie(
                "jwt", generate_jwt(user_query.username), httponly=True
            )
            response.set_cookie(
                "admin", ADMIN, httponly=True
            )
        return response
    return templates.TemplateResponse(
        "accounts/register.html", {
            "request": request,
            "form": form
        }
    )


async def login(request):
    """
    Validate form, login and authenticate user with JWT token
    """
    path = request.query_params['next']
    data = await request.form()
    form = LoginForm(data)
    username = form.username.data
    password = form.password.data
    if request.method == "POST" and form.validate():
        try:
            results = await User.get(
                username=username)
            hashed_password = results.password
            valid_password = check_password(password, hashed_password)
            if not valid_password:
                user_error = "Invalid username or password"
                return templates.TemplateResponse(
                    "accounts/login.html",
                    {
                        "request": request,
                        "form": form,
                        "user_error": user_error
                    },
                )
            # update login counter and login time
            results.login_count += 1
            results.last_login = datetime.datetime.now()
            await results.save()
            response = RedirectResponse(BASE_HOST + path, status_code=302)
            response.set_cookie(
                "jwt", generate_jwt(results.username), httponly=True
            )
            response.set_cookie(
                "admin", ADMIN, httponly=True
            )
            return response
        except:  # noqa
            user_error = "Please register you don't have account"
            return templates.TemplateResponse(
                "accounts/login.html",
                {
                    "request": request,
                    "form": form,
                    "user_error": user_error,
                },
            )
    return templates.TemplateResponse("accounts/login.html", {
        "request": request,
        "form": form,
        "path": path
    })


@requires("authenticated")
async def user_delete(request):
    """
    Delete user
    """
    id = request.path_params["id"]
    if request.method == "POST":
        async with in_transaction() as conn:
            await conn.execute_query(
                f'DELETE FROM tag WHERE tag.id IN \
                (SELECT question_tag.tag_id FROM question \
                JOIN question_tag ON question_tag.question_id = question.id \
                JOIN "user" ON "user".id = question.user_id \
                WHERE "user".id = {id})'
            )
        async with in_transaction() as conn:
            await conn.execute_query(
                f'UPDATE question SET accepted_answer = false \
                FROM answer, "user" WHERE question.id = answer.question_id \
                AND "user".id = {id} AND question.accepted_answer = true'
            )
        await User.get(id=id).delete()
        if request.user.username == ADMIN:
            return RedirectResponse(url="/accounts/dashboard", status_code=302)
        request.session.clear()
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie("jwt")
        return response


@requires(["authenticated", ADMIN], redirect="index")
async def dashboard(request):
    if request.user.is_authenticated:
        auth_user = request.user.display_name
        results = await User.all()
        questions = await Question.all().prefetch_related('user')
        answers = await Answer.all()
        return templates.TemplateResponse(
            "accounts/dashboard.html",
            {
                "request": request,
                "results": results,
                "questions": questions,
                "answers": answers,
                "auth_user": auth_user
            },
        )


@requires("authenticated", redirect="index")
async def profile(request):
    if request.user.is_authenticated:
        auth_user = request.user.display_name
        results = await User.get(username=auth_user)
        questions = await Question.all().filter(user_id=results.id)
        answers = await Answer.all().filter(ans_user_id=results.id)
        data = await request.form()
        print(data)
        return templates.TemplateResponse(
            "accounts/profile.html",
            {
                "request": request,
                "results": results,
                "auth_user": auth_user,
                "questions": questions,
                "answers": answers
            }
        )


async def logout(request):
    request.session.clear()
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("jwt")
    return response
