from starlette.routing import Route, Router
from accounts.views import (
    register,
    logout,
    login,
    profile,
    dashboard,
    user_delete
)


accounts_routes = Router([
    Route("/login", endpoint=login,
          methods=["GET", "POST"], name="login"),
    Route("/register", endpoint=register,
          methods=["GET", "POST"], name="register"),
    Route("/logout", endpoint=logout, methods=["GET", "POST"], name="logout"),
    Route("/profile", endpoint=profile, methods=["GET"], name="profile"),
    Route("/dashboard", endpoint=dashboard, methods=["GET"], name="dashboard"),
    Route("/user-delete/{id:int}", endpoint=user_delete,
          methods=["GET", "POST"], name="user_delete"),
])
