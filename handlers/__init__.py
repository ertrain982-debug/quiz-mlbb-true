from . import start, quiz, rating, profile, help

routers = [
    start.router,
    quiz.router,
    rating.router,
    profile.router,
    help.router
]